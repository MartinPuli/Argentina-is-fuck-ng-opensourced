"""Web app: a fictional PAMI with an internal side and a public side.

Internal (staff password): offices upload purchases, reviewers clear held files.
Public: the purchasing portal. It serves an attachment only if the gate cleared it.
"""

import hashlib
import io
import json
import os
import re
import secrets
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, urlsplit

import pymupdf
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from . import activity, agent, sanitize, llm, learning  # noqa: E402
from .detect import Finding, scan  # noqa: E402
from .policy import HOLD, PUBLIC, WITHHELD, decide, valid_image_analysis, valid_text_analysis  # noqa: E402
from .rules import RULES  # noqa: E402
from .store import Events, db  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures" / "pdfs"
OFFICES = ["UGL XXIII Jujuy", "UGL XXX Chivilcoy", "UGL XIX Misiones", "UGL VI Capital Federal"]
VISIBLE = ("public", "approved", "cleaned")
MAX_FILES = 8
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_PDF_PAGES = 50
MAX_REVIEW_NOTE = 2000

app = FastAPI(title="Publication Gate")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.filters["money"] = lambda v: f"$ {v:,.0f}".replace(",", ".")
templates.env.filters["fromjson"] = lambda v: json.loads(v) if v else None
templates.env.filters["web_url"] = lambda v: v if isinstance(v, str) and urlsplit(v).scheme in ("http", "https") else ""
templates.env.globals["RULES"] = RULES
events = Events()
basic = HTTPBasic(auto_error=False)
LIVE_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="gate-live")
LIVE_CAPACITY = threading.BoundedSemaphore(32)
STEP_READ = "Read"
STEP_SCAN = "Find IDs"
STEP_LEARN = "Learned rules"
STEP_AI = "AkashML AI"
STEP_VISION = "AkashML vision"
STEP_DECIDE = "Decide"
STEP_BRIEF = "Guild agent note"
STEP_CLEAN = "Clean copy"
STEP_VERIFY = "Guild verifier"
LABEL = {"public": "Cleared for publication", "approved": "Approved", "hold": "Needs review", "withheld": "Blocked",
         "cleaned": "Published cleaned copy"}


def origin_of(value: str, *, origin_header: bool = False) -> tuple | None:
    """Compare browser origins including scheme and effective port."""
    if not value or any(c.isspace() for c in value) or "\\" in value:
        return None
    try:
        parts = urlsplit(value)
        if (parts.scheme not in ("http", "https") or not parts.hostname
                or parts.username is not None or parts.password is not None):
            return None
        if origin_header and (parts.path or parts.query or parts.fragment):
            return None
        port = parts.port
        return parts.scheme, parts.hostname.lower(), port if port is not None else (443 if parts.scheme == "https" else 80)
    except ValueError:
        return None


@app.middleware("http")
async def same_origin_posts(request: Request, call_next):
    """Reject cross-site form posts (CSRF).

    Found by Semgrep: without this, any web page could make a reviewer's browser
    submit "Approve for public" and publish a held medical file.
    """
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        has_origin = "origin" in request.headers
        source = request.headers.get("origin") if has_origin else request.headers.get("referer", "")
        actual = origin_of(source or "", origin_header=has_origin)
        if actual is None or actual != origin_of(str(request.url)):
            return PlainTextResponse("cross-site request blocked", status_code=403)
    return await call_next(request)


def staff(creds: HTTPBasicCredentials | None = Depends(basic)) -> str:
    if os.getenv("GATE_OPEN_DEMO") == "1":
        return "reviewer"  # public hackathon demo: staff pages open, all data fictional
    password = os.getenv("GATE_STAFF_PASSWORD")
    if not password:
        raise HTTPException(503, "Staff access is disabled until GATE_STAFF_PASSWORD is configured.",
                            headers={"Cache-Control": "no-store"})
    username = os.getenv("GATE_STAFF_USERNAME") or "reviewer"
    username_ok = secrets.compare_digest((creds.username if creds else "").encode(), username.encode())
    password_ok = secrets.compare_digest((creds.password if creds else "").encode(), password.encode())
    if creds and username_ok and password_ok:
        return username
    raise HTTPException(401, "Staff credentials are required.",
                        headers={"WWW-Authenticate": 'Basic realm="Publication Gate staff"',
                                 "Cache-Control": "no-store"})


def safe_filename(filename: str) -> str:
    name = filename.replace("\\", "/").rsplit("/", 1)[-1]
    name = "".join(c for c in name if not unicodedata.category(c).startswith("C")).strip()
    return name[:200] or "attachment.pdf"


def pdf_response(pdf: bytes, filename: str) -> Response:
    name = safe_filename(filename)
    fallback = re.sub(r"[^a-zA-Z0-9_. -]", "_", name)
    return Response(pdf, media_type="application/pdf", headers={
        "Content-Disposition": f'inline; filename="{fallback}"; filename*=UTF-8\'\'{quote(name, safe="")}',
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    })


async def validated_uploads(files: list[UploadFile]) -> list[tuple[str, bytes]]:
    """Reject the complete batch before creating any public purchase metadata."""
    try:
        if not files or len(files) > MAX_FILES:
            raise HTTPException(400, f"Choose between 1 and {MAX_FILES} PDF attachments.")
        uploads = []
        total = 0
        for upload in files:
            data = await upload.read(MAX_FILE_BYTES + 1)
            if not data:
                raise HTTPException(400, "Every attachment must contain a PDF; empty files are not accepted.")
            total += len(data)
            if len(data) > MAX_FILE_BYTES or total > MAX_UPLOAD_BYTES:
                raise HTTPException(413, "Attachments exceed the per-file or combined upload size limit.")
            if not data.lstrip().startswith(b"%PDF-"):
                raise HTTPException(400, "Every attachment must be a readable PDF.")
            try:
                with pymupdf.open(stream=data, filetype="pdf") as document:
                    if document.needs_pass:
                        raise HTTPException(400, "Password-protected PDFs cannot be checked. Upload an unlocked copy.")
                    if not document.is_pdf or document.page_count < 1:
                        raise HTTPException(400, "Every attachment must contain at least one PDF page.")
                    if document.page_count > MAX_PDF_PAGES:
                        raise HTTPException(400, f"Each PDF must contain at most {MAX_PDF_PAGES} pages.")
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(400, "An attachment could not be read as a PDF. Check the file and retry.") from None
            uploads.append((safe_filename(upload.filename or "attachment.pdf"), data))
        return uploads
    finally:
        for upload in files:
            await upload.close()


def page(request: Request, name: str, **ctx) -> Response:
    ctx.setdefault("llm_on", llm.configured())
    ctx.setdefault("agent_on", agent.configured())
    ctx.setdefault("events_backend", events.backend)
    return templates.TemplateResponse(request, name, ctx)


def progress(job: dict | None, name: str, status: str, detail: str = "") -> None:
    if job is not None:
        activity.step(job, name, status, detail)


def evaluate(pdf: bytes, job: dict | None = None) -> tuple:
    started = time.perf_counter()
    active, rules_revision = learning.snapshot()
    progress(job, STEP_READ, "running")
    result = scan(pdf)
    progress(job, STEP_READ, "done", f"{len(result.pages)} page(s) read")
    progress(job, STEP_SCAN, "done", f"{len(result.findings)} initial finding(s)")
    before = len(result.findings)
    result.findings.extend(learning.apply(result.pages, active))
    progress(job, STEP_LEARN, "done", f"{len(active)} active rule(s); {len(result.findings) - before} finding(s)")
    progress(job, STEP_AI, "running")
    model = llm.review("\n\n".join(p.text for p in result.pages))
    progress(job, STEP_AI, "done" if valid_text_analysis(model) else "error",
             "Analysis returned" if valid_text_analysis(model) else "Required text analysis unavailable or incomplete")
    progress(job, STEP_VISION, "running" if any(p.image for p in result.pages) else "skipped")
    images = [llm.review_image(p.image) if p.image else None for p in result.pages]
    if any(p.image for p in result.pages):
        valid = all(valid_image_analysis(images[i]) for i, p in enumerate(result.pages) if p.image)
        progress(job, STEP_VISION, "done" if valid else "error",
                 "Analysis returned" if valid else "Required image analysis unavailable or incomplete")
    decision, reasons, findings = decide(result, model, images)
    progress(job, STEP_DECIDE, "done", LABEL[decision])
    if job is not None:
        activity.finish(job, why={PUBLIC: "Current checks found no reason to restrict publication.",
                                  HOLD: "A person must review this attachment before publication.",
                                  WITHHELD: "A blocking finding keeps this attachment private."}[decision])
    return model, decision, reasons, findings, (time.perf_counter() - started) * 1000, rules_revision


def gate_files(purchase: dict, files: list[tuple[str, bytes]]) -> None:
    """Check all attachments of a purchase in parallel, then store them in order."""
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda f: evaluate(f[1]), files))
    for (filename, pdf), evaluated in zip(files, results):
        store_attachment(purchase, filename, pdf, *evaluated)


def store_attachment(purchase: dict, filename: str, pdf: bytes, model, decision, reasons,
                     findings, latency, rules_revision=None, job: dict | None = None) -> int:
    """Store one checked file and log the decision."""
    # Phrases the model wants removed carry raw personal data: used to redact, never stored.
    phrases = model.pop("identifying_phrases", []) if isinstance(model, dict) else []
    with db() as con:
        cur = con.execute(
            "insert into attachments (purchase_id, filename, sha256, pdf, decision, reasons,"
            " findings, model, created_at) values (?,?,?,?,?,?,?,?,?)",
            (purchase["id"], filename, hashlib.sha256(pdf).hexdigest(), pdf, decision,
             json.dumps(reasons), json.dumps(findings), json.dumps(model), time.time()),
        )
        att_id = cur.lastrowid
    # A policy change during analysis leaves the file stale until explicitly rechecked.
    try:
        learning.record_check(att_id, rules_revision if rules_revision is not None else learning.revision())
    except ValueError:
        pass
    events.log("decision", purchase["office"], purchase["id"], att_id, filename, decision,
               sorted({f["kind"] for f in findings}), "gate", latency)
    if job is not None:
        activity.finish(job, attachment_id=att_id, decision=decision)
    candidate = None
    if decision != PUBLIC:
        try:
            candidate = sanitize.build(pdf, findings, phrases if isinstance(phrases, list) else [], decision)
        except Exception:
            candidate = None
    if candidate is not None and candidate.verified:
        with db() as con:
            con.execute("update attachments set public_pdf=?, manifest=? where id=?",
                        (candidate.pdf, json.dumps(candidate.manifest), att_id))
        progress(job, STEP_CLEAN, "done", f"{len(candidate.manifest)} item(s) removed")
        events.log("cleaned_copy", purchase["office"], purchase["id"], att_id, filename, decision,
                   sorted({m["category"] for m in candidate.manifest}), "sanitizer", 0)
        if agent.configured():
            progress(job, STEP_VERIFY, "running")
            threading.Thread(target=verify_in_background, args=(att_id, purchase, filename, candidate, job),
                             daemon=True).start()
            return att_id
    if decision != PUBLIC and agent.configured():
        progress(job, STEP_BRIEF, "running")
        threading.Thread(target=brief_in_background, args=(att_id, purchase, filename, decision,
                                                           reasons, findings, job), daemon=True).start()
    elif job is not None:
        activity.finish(job, done=True)
    return att_id


def verify_in_background(att_id, purchase, filename, candidate, job=None) -> None:
    """Two independent checks must agree before a cleaned copy goes public on its own."""
    try:
        result = agent.verify(candidate.text, candidate.manifest)
        new = "cleaned" if result["verdict"] == "PASS" and candidate.verified else HOLD
        with db() as con:
            con.execute("update attachments set verifier=?, decision=? where id=?",
                        (json.dumps(result), new, att_id))
        events.log("verifier", purchase["office"], purchase["id"], att_id, filename, new,
                   [result["verdict"].lower()], "guild-verifier", result.get("latency_ms", 0))
        progress(job, STEP_VERIFY, "done" if result["verdict"] == "PASS" else "error",
                 {"PASS": "Agrees: nothing identifies a person", "FAIL": result["text"][:80]}.get(result["verdict"], "Unavailable"))
        if job is not None:
            activity.finish(job, decision=new, agent_url=result.get("url", ""),
                            why={"cleaned": f"Published without {', '.join(sorted({m['category'] for m in candidate.manifest}))}.",
                                 HOLD: "The verifier did not agree. A person must review the cleaned copy."}[new])
    except Exception:
        progress(job, STEP_VERIFY, "error", "Verifier unavailable; file stays private")
    finally:
        if job is not None:
            activity.finish(job, done=True)


def brief_in_background(att_id, purchase, filename, decision, reasons, findings, job=None) -> None:
    try:
        brief = agent.brief(purchase, filename, decision, reasons, findings)
        with db() as con:
            con.execute("update attachments set agent=? where id=?", (json.dumps(brief), att_id))
        events.log("agent_brief", purchase["office"], purchase["id"], att_id, filename, decision,
                   [], "guild-agent", brief.get("latency_ms", 0))
        progress(job, STEP_BRIEF, "error" if "error" in brief else "done",
                 "Unavailable" if "error" in brief else "Ready")
        if job is not None:
            activity.finish(job, agent_url=brief.get("url", ""))
    except Exception:
        progress(job, STEP_BRIEF, "error", "Agent note unavailable; publication decision unchanged")
    finally:
        if job is not None:
            activity.finish(job, done=True)


def create_purchase(office: str, procedure: str, item: str, amount: float, actor: str = "office") -> dict:
    with db() as con:
        cur = con.execute(
            "insert into purchases (office, procedure, item, amount, created_at) values (?,?,?,?,?)",
            (office, procedure, item, amount, time.time()))
        purchase = {"id": cur.lastrowid, "office": office}
    events.log("submitted", office, purchase["id"], actor=actor)
    return purchase


def reserve_live(count: int) -> None:
    """Bound queued PDF memory as well as concurrent processing."""
    acquired = 0
    for _ in range(count):
        if not LIVE_CAPACITY.acquire(blocking=False):
            for _ in range(acquired):
                LIVE_CAPACITY.release()
            raise HTTPException(503, "The live queue is full. Wait for current checks to finish and retry.")
        acquired += 1


def process_live(purchase: dict, filename: str, pdf: bytes, job: dict) -> None:
    try:
        try:
            evaluated = evaluate(pdf, job)
        except Exception:
            # An unexpected worker failure must not erase a block found before it failed.
            # Ordinary missing providers are handled by decide() as HOLD, not here.
            progress(job, STEP_DECIDE, "error", "Processing failed; file remains private")
            activity.finish(job, why="Processing failed. Inspect the private file and submit it again.")
            evaluated = (None, WITHHELD, ["Processing failed. The attachment remains private."],
                         [{"kind": "processing_failed", "label": "Document processing failed",
                           "evidence": "", "page": 0, "severity": "block", "rule": "unreadable"}],
                         0, "")
        store_attachment(purchase, filename, pdf, *evaluated, job=job)
    except Exception:
        # Storage/audit errors are not converted into an assumed safe verdict.
        progress(job, STEP_DECIDE, "error", "Could not complete the check; inspect the purchase")
        activity.finish(job, done=True, decision="error", why="The check did not complete.")
    finally:
        LIVE_CAPACITY.release()


def queue_live(purchase: dict, item: str, files: list[tuple[str, bytes]], actor: str) -> None:
    """Submit an already validated batch with capacity reserved by its caller."""
    for filename, pdf in files:
        job = activity.start(purchase, item, filename,
                             [STEP_READ, STEP_SCAN, STEP_LEARN, STEP_AI, STEP_VISION, STEP_DECIDE])
        activity.finish(job, actor=actor)
        try:
            LIVE_EXECUTOR.submit(process_live, purchase, filename, pdf, job)
        except Exception:
            LIVE_CAPACITY.release()
            progress(job, STEP_DECIDE, "error", "Could not queue this attachment; submit it again")
            activity.finish(job, done=True, decision="error", why="The attachment was not processed.")


@app.get("/live")
def live_view(request: Request, user: str = Depends(staff)):
    return page(request, "live.html", offices=OFFICES, user=user)


@app.post("/live/upload")
async def live_upload(office: str = Form(...), procedure: str = Form(...), item: str = Form(...),
                      amount: float = Form(...), files: list[UploadFile] = File(...),
                      user: str = Depends(staff)):
    uploads = await validated_uploads(files)
    reserve_live(len(uploads))
    try:
        purchase = create_purchase(office, procedure, item, amount, actor=user)
    except Exception:
        for _ in uploads:
            LIVE_CAPACITY.release()
        raise
    queue_live(purchase, item, uploads, user)
    return RedirectResponse("/live", status_code=303)


@app.post("/live/demo/seed")
async def live_demo_seed(user: str = Depends(staff)):
    prepared = []
    for spec in json.loads((FIXTURES / "purchases.json").read_text()):
        files = [UploadFile(io.BytesIO((FIXTURES / name).read_bytes()), filename=name) for name in spec["files"]]
        prepared.append((spec, await validated_uploads(files)))
    count = sum(len(files) for _, files in prepared)
    reserve_live(count)
    remaining = count
    try:
        for spec, uploads in prepared:
            purchase = create_purchase(spec["office"], spec["procedure"], spec["item"], spec["amount"], actor=user)
            queue_live(purchase, spec["item"], uploads, user)
            remaining -= len(uploads)
    finally:
        for _ in range(remaining):
            LIVE_CAPACITY.release()
    return RedirectResponse("/live", status_code=303)


@app.post("/live/reset")
def live_reset(user: str = Depends(staff)):
    """Clear demo purchases and files between takes. Learned rules and the audit history stay."""
    if activity.running():
        return PlainTextResponse("Files are still being checked. Wait for them to finish, then reset.",
                                 status_code=409)
    with db() as con:
        con.execute("create table if not exists learning_checks (attachment_id integer primary key, "
                    "revision text not null, checked_at real not null)")
        con.execute("delete from learning_checks")
        con.execute("delete from attachments")
        con.execute("delete from purchases")
    activity.clear()
    events.log("demo_reset", "", 0, actor=user)
    return RedirectResponse("/live", status_code=303)


@app.get("/api/activity")
def api_activity(user: str = Depends(staff)):
    """Staff-only progress; only current publication decisions count as published."""
    # A done job implies its row was committed before this database read.
    jobs = activity.snapshot()
    with db() as con:
        rows = con.execute("select a.id,a.filename,a.decision,a.findings,a.agent,a.manifest,"
                           "a.public_pdf is not null as has_clean,p.office,p.item,p.id as pid from attachments a "
                           "join purchases p on p.id=a.purchase_id order by a.id").fetchall()
    current = {row["id"]: learning.current(row["id"]) for row in rows}
    by_id = {row["id"]: row for row in rows}
    counts = {"published": 0, "waiting": 0, "blocked": 0, "stale": 0, "processing": 0}
    waiting = []
    for row in rows:
        is_current = current[row["id"]]
        counts["stale"] += not is_current
        if row["decision"] in VISIBLE and is_current:
            counts["published"] += 1
        elif row["decision"] == WITHHELD:
            counts["blocked"] += 1
        elif row["decision"] == HOLD:
            counts["waiting"] += 1
            findings = json.loads(row["findings"] or "[]")
            brief = json.loads(row["agent"] or "null") or {}
            waiting.append({"id": row["id"], "file": row["filename"], "office": row["office"],
                            "item": row["item"], "pid": row["pid"],
                            "why": sorted({f["label"] for f in findings}), "risk": "",
                            "note": brief.get("text", ""), "agent_url": brief.get("url", ""),
                            "current": is_current, "can_approve": is_current,
                            "has_clean": bool(row["has_clean"]),
                            "removed": sorted({m["category"] for m in json.loads(row["manifest"] or "[]")})})
    for job in jobs:
        row = by_id.get(job["attachment_id"])
        job["current"] = current.get(job["attachment_id"], False)
        job["stale"] = row is not None and not job["current"]
        job["recorded_decision"] = row["decision"] if row else job["decision"]
        if row:
            job["decision"] = "stale" if job["stale"] and row["decision"] in VISIBLE else row["decision"]
            if job["stale"]:
                job["why"] = "Recheck against the current rules before publication."
        counts["processing"] += not job["done"]
    return JSONResponse({"jobs": jobs, "counts": counts, "waiting": waiting},
                        headers={"Cache-Control": "no-store"})


@app.get("/exposures")
def exposures(request: Request, user: str = Depends(staff)):
    from .exposure_data import COMPARISON_NOTE, EXPOSURES, RESEARCH_WINDOW, REVIEWED_AT
    return page(request, "exposures.html", user=user,
                companies=[row for row in EXPOSURES if row["entity_type"] == "company"],
                public_bodies=[row for row in EXPOSURES if row["entity_type"] == "public_body"],
                research_window=RESEARCH_WINDOW, reviewed_at=REVIEWED_AT, comparison_note=COMPARISON_NOTE)


@app.get("/")
def home(request: Request):
    return page(request, "home.html")


@app.get("/office")
def office_form(request: Request, user: str = Depends(staff)):
    return page(request, "office.html", offices=OFFICES)


@app.post("/office")
async def office_submit(office: str = Form(...), procedure: str = Form(...), item: str = Form(...),
                        amount: float = Form(...), files: list[UploadFile] = File(...),
                        user: str = Depends(staff)):
    uploads = await validated_uploads(files)
    purchase = create_purchase(office, procedure, item, amount, actor=user)
    gate_files(purchase, uploads)
    return RedirectResponse(f"/purchase/{purchase['id']}", status_code=303)


@app.post("/demo/seed")
def demo_seed(user: str = Depends(staff)):
    first = None
    for p in json.loads((FIXTURES / "purchases.json").read_text()):
        purchase = create_purchase(p["office"], p["procedure"], p["item"], p["amount"], actor=user)
        first = first or purchase["id"]
        gate_files(purchase, [(name, (FIXTURES / name).read_bytes()) for name in p["files"]])
    return RedirectResponse(f"/purchase/{first}", status_code=303)


@app.get("/purchase/{pid}")
def purchase_view(request: Request, pid: int, user: str = Depends(staff)):
    with db() as con:
        purchase = con.execute("select * from purchases where id=?", (pid,)).fetchone()
        if not purchase:
            raise HTTPException(404)
        atts = con.execute("select * from attachments where purchase_id=? order by id", (pid,)).fetchall()
    return page(request, "purchase.html", purchase=purchase, atts=atts,
                stale_ids={a["id"] for a in atts if not learning.current(a["id"])})


@app.get("/review")
def review_queue(request: Request, user: str = Depends(staff)):
    with db() as con:
        held = con.execute(
            "select a.*, p.office, p.procedure, p.item from attachments a join purchases p "
            "on p.id=a.purchase_id where a.decision='hold' order by a.id").fetchall()
        done = con.execute(
            "select a.*, p.office from attachments a join purchases p on p.id=a.purchase_id "
            "where a.reviewed_by is not null order by a.reviewed_at desc limit 10").fetchall()
    return page(request, "review.html", held=held, done=done, user=user,
                stale_ids={a["id"] for a in held if not learning.current(a["id"])})


@app.post("/review/{att_id}")
def review_decide(att_id: int, action: str = Form(...), reviewer: str = Form(""),
                  note: str = Form(""), user: str = Depends(staff)):
    if action == "approve" and not learning.current(att_id):
        raise HTTPException(409, "Recheck this file against the current rules before approving publication.")
    if action not in ("approve", "reject"):
        raise HTTPException(400, "A valid review action is required.")
    if not note.strip() or len(note.strip()) > MAX_REVIEW_NOTE:
        raise HTTPException(400, f"Explain the decision in 1–{MAX_REVIEW_NOTE} characters.")
    new = "approved" if action == "approve" else WITHHELD
    with db() as con:
        row = con.execute("select a.*, p.office from attachments a join purchases p on "
                          "p.id=a.purchase_id where a.id=? and a.decision='hold'", (att_id,)).fetchone()
        if not row:
            raise HTTPException(409, "not waiting for review")
        updated = con.execute("update attachments set decision=?, reviewed_by=?, reviewed_at=?, review_note=?"
                              " where id=? and decision='hold'", (new, user, time.time(), note.strip(), att_id))
        if updated.rowcount != 1:
            raise HTTPException(409, "not waiting for review")
    waited = (time.time() - row["created_at"]) * 1000
    events.log("approved" if new == "approved" else "rejected", row["office"], row["purchase_id"],
               att_id, row["filename"], new, [], user, waited)
    return RedirectResponse("/review", status_code=303)


@app.get("/public")
def public_portal(request: Request):
    with db() as con:
        purchases = con.execute("select * from purchases order by id desc").fetchall()
        atts = con.execute("select id, purchase_id, filename, decision,"
                           " public_pdf is not null as cleaned from attachments").fetchall()
    by_purchase: dict[int, dict] = {}
    for a in atts:
        slot = by_purchase.setdefault(a["purchase_id"], {"files": [], "kept": 0, "pending": 0})
        if a["decision"] in VISIBLE and learning.current(a["id"]):
            slot["files"].append(a)
        elif a["decision"] == "hold" or a["decision"] in VISIBLE:
            slot["pending"] += 1
        else:
            slot["kept"] += 1
    return page(request, "public.html", purchases=purchases, by_purchase=by_purchase)


@app.get("/public/file/{att_id}")
def public_file(att_id: int):
    """The enforcement point. Checked on every request, not at upload time only."""
    with db() as con:
        row = con.execute("select filename, pdf, public_pdf, decision from attachments where id=?", (att_id,)).fetchone()
    if not row or row["decision"] not in VISIBLE or not learning.current(att_id):
        raise HTTPException(404, headers={"Cache-Control": "no-store"})
    # When a cleaned copy exists, it is the only version that can ever be public.
    return pdf_response(row["public_pdf"] or row["pdf"], row["filename"])


@app.get("/internal/file/{att_id}")
def internal_file(att_id: int, user: str = Depends(staff)):
    with db() as con:
        row = con.execute("select filename, pdf from attachments where id=?", (att_id,)).fetchone()
    if not row:
        raise HTTPException(404, headers={"Cache-Control": "no-store"})
    return pdf_response(row["pdf"], row["filename"])


@app.get("/internal/clean/{att_id}")
def internal_clean(att_id: int, user: str = Depends(staff)):
    """Staff preview of the cleaned copy, whatever the decision."""
    with db() as con:
        row = con.execute("select filename, public_pdf from attachments where id=?", (att_id,)).fetchone()
    if not row or not row["public_pdf"]:
        raise HTTPException(404, headers={"Cache-Control": "no-store"})
    return pdf_response(row["public_pdf"], row["filename"])


@app.get("/dashboard")
def dashboard(request: Request, user: str = Depends(staff)):
    return page(request, "dashboard.html", s=events.stats(), h=events.history())


@app.get("/api/rules")
def api_rules():
    return RULES


# Incident evidence generates candidates. Only reviewed, tested rules affect PDFs.
from .learning_sources import CASES
from .learning_proposer import UNVERIFIED, propose
from .skill_export import render_skill, render_proposal


def learning_rule(rule_id: int) -> dict:
    rule = learning.get_rule(rule_id)
    if not rule:
        raise HTTPException(404, "Rule not found.")
    return rule


@app.get("/learning")
def learning_home(request: Request, user: str = Depends(staff)):
    rules = learning.list_rules()
    return page(request, "learning.html", cases=CASES, rules=rules,
                active_count=sum(r["status"] == "active" for r in rules),
                pending_count=learning.pending_count(), user=user)


@app.post("/learning/from-case/{case_id}")
def learn_from_case(case_id: str, user: str = Depends(staff)):
    case = next((c for c in CASES if c["id"] == case_id), None)
    if case is None:
        raise HTTPException(404, "Source case not found.")
    source = {k: case[k] for k in ("title", "url", "evidence_status", "summary")}
    try:
        spec, generator = propose(source, recipe=case["recipe"])
        ident = learning.create_candidate(spec, source, user, generator=generator)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    events.log("rule_proposed", "Learning library", 0, actor=user)
    return RedirectResponse(f"/learning/rules/{ident}", status_code=303)


@app.post("/learning/propose")
def learn_from_report(title: str = Form(..., min_length=3, max_length=160),
                      url: str = Form(..., max_length=1000),
                      evidence_status: str = Form(..., max_length=80),
                      summary: str = Form(..., min_length=30, max_length=5800),
                      user: str = Depends(staff)):
    if evidence_status not in {"reported", "acknowledged", "alleged", "unknown"}:
        raise HTTPException(400, "Choose a valid source evidence status.")
    source = {"title": title, "url": url, "evidence_status": UNVERIFIED,
              "summary": f"Submitter describes evidence as: {evidence_status}.\n\n{summary}"}
    try:
        spec, generator = propose(source)
        ident = learning.create_candidate(spec, source, user, generator=generator)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    events.log("rule_proposed", "Learning library", 0, actor=user)
    return RedirectResponse(f"/learning/rules/{ident}", status_code=303)


@app.get("/learning/rules/{rule_id}")
def learning_detail(request: Request, rule_id: int, user: str = Depends(staff)):
    return page(request, "learning_rule.html", rule=learning_rule(rule_id),
                pending_count=learning.pending_count(), user=user)


@app.post("/learning/rules/{rule_id}/test")
def test_learning_rule(rule_id: int, user: str = Depends(staff)):
    learning_rule(rule_id)
    try:
        learning.run_tests(rule_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    events.log("rule_tested", "Learning library", 0, actor=user)
    return RedirectResponse(f"/learning/rules/{rule_id}", status_code=303)


@app.post("/learning/rules/{rule_id}/activate")
def activate_learning_rule(rule_id: int, digest: str = Form(...), user: str = Depends(staff)):
    learning_rule(rule_id)
    try:
        learning.activate(rule_id, digest, user)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    events.log("rule_activated", "Learning library", 0, actor=user)
    return RedirectResponse(f"/learning/rules/{rule_id}", status_code=303)


@app.post("/learning/rules/{rule_id}/retire")
def retire_learning_rule(rule_id: int, digest: str = Form(...), user: str = Depends(staff)):
    learning_rule(rule_id)
    try:
        learning.deactivate(rule_id, digest, user)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    events.log("rule_retired", "Learning library", 0, actor=user)
    return RedirectResponse(f"/learning/rules/{rule_id}", status_code=303)


@app.post("/learning/rescan")
def rescan_learning_rules(user: str = Depends(staff)):
    from dataclasses import asdict
    active, checked_revision = learning.snapshot()
    with db() as con:
        attachments = con.execute("select * from attachments order by id").fetchall()
    for attachment in attachments:
        scanned = scan(attachment["pdf"])
        found = list(scanned.findings) + learning.apply(scanned.pages, active)
        if (not scanned.pages or scanned.coverage_issues
                or any(p.coverage_issues for p in scanned.pages)):
            found.append(Finding("incomplete_recheck", "Recheck coverage is incomplete", "",
                                 0, "review", "unreadable"))
        decision = attachment["decision"]
        if any(f.severity == "block" for f in found):
            decision = WITHHELD
        elif any(f.severity == "review" for f in found) and decision in VISIBLE:
            decision = "hold"
        previous_findings = json.loads(attachment["findings"] or "[]")
        merged = list(previous_findings)
        for finding in found:
            item = asdict(finding)
            if item not in merged:
                merged.append(item)
        reasons = json.loads(attachment["reasons"] or "[]")
        if decision != attachment["decision"]:
            reasons.append("Rechecking against the current rules restricted publication. A previous approval no longer applies.")
        with db() as con:
            con.execute("BEGIN IMMEDIATE")
            current_row = con.execute("select decision from attachments where id=?", (attachment["id"],)).fetchone()
            # A concurrent review/recheck must never be overwritten with a weaker decision.
            strictness = {"public": 0, "approved": 0, "hold": 1, "withheld": 2}
            if strictness.get(current_row["decision"], 2) >= strictness.get(decision, 2):
                decision = current_row["decision"]
            con.execute("update attachments set decision=?,findings=?,reasons=? where id=?",
                        (decision, json.dumps(merged), json.dumps(reasons), attachment["id"]))
        try:
            learning.record_check(attachment["id"], checked_revision)
        except ValueError:
            raise HTTPException(409, "Rules changed during the recheck. Unchecked files remain unavailable. Run the recheck again.") from None
        events.log("rule_recheck", "Learning library", attachment["purchase_id"],
                   attachment["id"], attachment["filename"], decision,
                   sorted({f.kind for f in found}), user)
    return RedirectResponse("/learning", status_code=303)


def learning_download(body: str | bytes, filename: str, media_type: str) -> Response:
    return Response(body, media_type=media_type, headers={
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
    })


@app.get("/learning/rules/{rule_id}/skill.md")
def download_learning_skill(rule_id: int, user: str = Depends(staff)):
    return learning_download(render_skill(learning_rule(rule_id)), f"rule-{rule_id}-SKILL.md", "text/markdown")


@app.get("/learning/rules/{rule_id}/proposal.md")
def download_learning_proposal(rule_id: int, user: str = Depends(staff)):
    return learning_download(render_proposal(learning_rule(rule_id)), f"rule-{rule_id}-PROPOSAL.md", "text/markdown")


@app.get("/learning/rules/{rule_id}/bundle.zip")
def download_learning_bundle(rule_id: int, user: str = Depends(staff)):
    import io
    import zipfile
    rule = learning_rule(rule_id)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("SKILL.md", render_skill(rule))
        bundle.writestr("PROPOSAL.md", render_proposal(rule))
        bundle.writestr("evidence.json", json.dumps(rule, indent=2, ensure_ascii=False))
    return learning_download(buffer.getvalue(), f"publication-rule-{rule_id}.zip", "application/zip")


@app.get("/learning/rules/{rule_id}/example/{index}.pdf")
def download_learning_example(rule_id: int, index: int, user: str = Depends(staff)):
    rule = learning_rule(rule_id)
    examples = rule["spec"]["tests"]
    if index < 0 or index >= len(examples):
        raise HTTPException(404, "Example not found.")
    with pymupdf.open() as document:
        sheet = document.new_page()
        text = "FICTIONAL TEST DOCUMENT / DATOS FICTICIOS\n\n" + examples[index]["text"]
        unused = sheet.insert_textbox(pymupdf.Rect(50, 50, 545, 790), text, fontsize=11)
        if unused < 0:
            raise HTTPException(400, "This example is too long for the printable fixture. Use its text from the evidence bundle.")
        content = document.tobytes()
    return pdf_response(content, f"fictional-rule-{rule_id}-example-{index}.pdf")
