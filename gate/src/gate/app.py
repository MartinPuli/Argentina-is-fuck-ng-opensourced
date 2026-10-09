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
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote, urlsplit

import pymupdf
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from . import activity, agent, sanitize, llm, learning, pi_context, senso_context, incident_discovery, intake  # noqa: E402
from .detect import Finding, scan  # noqa: E402
from .policy import HOLD, PUBLIC, WITHHELD, decide, valid_image_analysis, valid_text_analysis  # noqa: E402
from .rules import RULES, model_guidelines  # noqa: E402
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



@asynccontextmanager
async def lifespan(_app):
    sweep_orphaned_holds()  # no background job survives a restart
    yield


app = FastAPI(title="Publication Gate", lifespan=lifespan)
STATIC = Path(__file__).parent / "static"
app.mount("/assets", StaticFiles(directory=STATIC, check_dir=False), name="assets")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def asset_url(name: str) -> str:
    """Content-versioned URL so a CDN never keeps serving a stale bundle or a cached 404 after a deploy."""
    try:
        version = hashlib.sha256((STATIC / name).read_bytes()).hexdigest()[:12]
    except OSError:
        version = "missing"
    return f"/assets/{name}?v={version}"


templates.env.globals["asset_url"] = asset_url
templates.env.filters["money"] = lambda v: "Not specified" if v is None else f"$ {v:,.0f}".replace(",", ".")
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
STEP_CLEARANCE = "Clearance levels"
LABEL = {"public": "Cleared for publication", "approved": "Approved", "hold": "Needs review", "withheld": "Blocked",
         "cleaned": "Published cleaned copy"}


def autonomous() -> bool:
    """GATE_AUTONOMOUS=1: every upload ends without a person; uncertainty restricts, never publishes."""
    return os.getenv("GATE_AUTONOMOUS") == "1"


_PENDING: dict[int, int] = {}
_PENDING_LOCK = threading.Lock()


def run_in_background(att_id: int, target, args: tuple) -> None:
    """Start a background step and count it, so only the last one to finish settles the file."""
    with _PENDING_LOCK:
        _PENDING[att_id] = _PENDING.get(att_id, 0) + 1
    try:
        threading.Thread(target=target, args=args, daemon=True).start()
    except Exception:
        background_done(att_id)
        raise


def background_done(att_id: int) -> None:
    with _PENDING_LOCK:
        left = _PENDING.get(att_id, 1) - 1
        if left > 0:
            _PENDING[att_id] = left
            return
        _PENDING.pop(att_id, None)
    settle(att_id)


def settle(att_id: int) -> bool:
    """With the flag on, a file still waiting for a person is restricted instead. Never publishes."""
    if not autonomous():
        return False
    with _PENDING_LOCK:
        if _PENDING.get(att_id):
            return False
    try:
        with db() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("select a.purchase_id,a.filename,a.decision,a.reasons,a.findings,a.reviewed_by,"
                              "p.office from attachments a left join purchases p on p.id=a.purchase_id "
                              "where a.id=?", (att_id,)).fetchone()
            if row is None or row["decision"] != HOLD or row["reviewed_by"] is not None:
                return False
            reasons = json.loads(row["reasons"] or "[]")
            findings = json.loads(row["findings"] or "[]")
            original = " ".join(r for r in reasons if isinstance(r, str)).strip().rstrip(".")
            rule = next((f.get("rule") for f in findings if isinstance(f, dict)
                         and f.get("severity") == "review" and f.get("rule") in RULES), "unreadable")
            reasons.append(f"Restricted automatically: {original or 'required checks did not clear publication'}."
                           " The original stays in the internal record.")
            findings.append({"kind": "autopilot_restricted", "label": "Restricted automatically", "evidence": "",
                             "page": 0, "severity": "review", "rule": rule})
            con.execute("update attachments set decision=?, reasons=?, findings=? where id=? and decision=?"
                        " and reviewed_by is null", (WITHHELD, json.dumps(reasons), json.dumps(findings), att_id, HOLD))
        events.log("autopilot", row["office"] or "", row["purchase_id"], att_id, row["filename"], WITHHELD,
                   ["autopilot_restricted"], "autopilot", 0)
        activity.emit(None, "Autopilot", "settle", WITHHELD, "restricted automatically", file=row["filename"])
        return True
    except Exception:
        return False  # the startup sweep is the safety net


def sweep_orphaned_holds() -> int:
    """Startup: no in-memory job survives a restart, so every unreviewed hold is settled."""
    if not autonomous():
        return 0
    with db() as con:
        ids = [r["id"] for r in con.execute(
            "select id from attachments where decision=? and reviewed_by is null order by id", (HOLD,))]
    return sum(settle(att_id) for att_id in ids)


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


def public_filename(purchase_id: int, att_id: int) -> str:
    """Neutral public name; the original upload name may carry personal data."""
    return f"compra-{int(purchase_id)}-adjunto-{int(att_id)}.pdf"


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
    checked_revision = rules_revision if rules_revision is not None else learning.revision()
    try:
        learning.record_check(att_id, checked_revision)
    except ValueError:
        pass
    with db() as con:
        verification_state = verifier_state(con, att_id)
    events.log("decision", purchase["office"], purchase["id"], att_id, filename, decision,
               sorted({f["kind"] for f in findings}), "gate", latency)
    if job is not None:
        activity.finish(job, attachment_id=att_id, decision=decision)
    if decision != PUBLIC:
        threading.Thread(target=senso_lookup, args=(att_id, findings, job), daemon=True).start()
    candidate = None
    phrases = phrases if isinstance(phrases, list) else []
    if decision != PUBLIC and agent.configured() and sanitize.text_only(pdf) and sanitize.cleanable(findings, decision):
        # Guild decides what each clearance level may see; the app applies it for real.
        progress(job, STEP_CLEARANCE, "running")
        run_in_background(att_id, clearance_in_background,
                          (att_id, purchase, filename, pdf, findings, phrases, decision,
                           checked_revision, verification_state, job))
        return att_id
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
            run_in_background(att_id, verify_in_background,
                              (att_id, purchase, filename, candidate, decision, checked_revision,
                               verification_state, hashlib.sha256(candidate.pdf).hexdigest(), job))
            return att_id
    if decision != PUBLIC and agent.configured():
        progress(job, STEP_BRIEF, "running")
        run_in_background(att_id, brief_in_background,
                          (att_id, purchase, filename, decision, reasons, findings, job))
        return att_id
    settle(att_id)
    if job is not None:
        activity.finish(job, done=True)
    return att_id


def senso_lookup(att_id: int, findings: list[dict], job: dict | None = None) -> dict:
    """Cite the governing guideline from Senso. Runs after the decision is stored."""
    result = senso_context.cite(att_id, findings)
    cited = result.get("status") == "cited"
    activity.emit(job, "Senso", "rule lookup", "done" if cited else "skipped",
                  ", ".join(result.get("rule_ids", [])) if cited else "unavailable; decision unchanged",
                  result.get("latency_ms"), file=str(att_id))
    return result


def verifier_state(con, att_id: int) -> dict | None:
    row = con.execute(
        "select a.decision,a.findings,a.reasons,a.reviewed_by,a.reviewed_at,a.review_note,a.verifier,a.clearance,"
        "c.revision,c.checked_at from attachments a left join learning_checks c on c.attachment_id=a.id "
        "where a.id=?", (att_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def clearance_in_background(att_id, purchase, filename, pdf, findings, phrases, decision,
                            expected_revision, expected_state, job=None) -> None:
    """Orchestrator -> public agent <-> public reviewer on Guild, then sanitize's own check.

    "cleaned" only when the reviewer said PASS and the detectors find nothing in the bytes
    we would publish. Anything else keeps the file private, with the cleaned copy saved
    for a human.
    """
    activity.bind(job)
    # The reason must match the decision that stays in place when clearance does not finish.
    new, url = decision, ""
    why = ("Clearance agents unavailable. A blocking finding keeps this attachment private."
           if decision == WITHHELD else "Clearance agents unavailable. A person must review the file.")
    try:
        with pymupdf.open(stream=pdf, filetype="pdf") as document:
            text = "\n".join(page.get_text() for page in document)
        last: dict = {}

        def render(remove):
            last["c"] = sanitize.build(pdf, findings, phrases + remove, decision)
            return last["c"].text if last["c"] is not None else None

        result = agent.clearance(text, findings, render=render,
                                 on_step=lambda name, status, detail: progress(job, name, status, detail))
        plan = agent.safe_plan(result)
        url = next((s["url"] for s in result.get("sessions", []) if s["agent"] == "orchestrator"), "")
        public = (result.get("levels") or {}).get("public") or {}
        candidate = last.get("c")
        candidate_clear = False
        if candidate is not None and candidate.verified is True:
            active, candidate_revision = learning.snapshot()
            checked = scan(candidate.pdf)
            found = list(checked.findings) + learning.apply(checked.pages, active)
            complete = (bool(checked.pages) and not checked.coverage_issues
                        and all(p.text.strip() and not p.coverage_issues and not p.has_images
                                and not p.image and p.source == "text" for p in checked.pages))
            candidate_clear = (candidate_revision == expected_revision and complete
                               and not any(f.severity in {"block", "review"} for f in found))
        procurement = None
        proc_remove = ((result.get("levels") or {}).get("procurement") or {}).get("remove", [])
        if "error" not in result:
            try:
                procurement = sanitize.build(pdf, findings, proc_remove, decision)
            except Exception:
                procurement = None
        if "error" in result:
            progress(job, STEP_CLEARANCE, "error", "Guild unavailable; file stays private")
        elif public.get("review") == "PASS" and candidate_clear:
            new = "cleaned"
            why = f"Published without {', '.join(sorted({m['category'] for m in candidate.manifest}))}."
        elif candidate_clear:
            new, why = HOLD, "The review did not pass. A person must review the cleaned copy."
        else:
            why = "Current checks did not clear the candidate. The existing restriction remains."
        if "error" not in result:
            progress(job, STEP_CLEARANCE, "done" if new == "cleaned" else "error",
                     f"{public.get('rounds', 0)} round(s) · {public.get('review', 'FAIL')}"
                     + ("" if candidate is None or candidate.verified else " · detectors disagree"))
        with db() as con:
            con.execute("BEGIN IMMEDIATE")
            state = verifier_state(con, att_id)
            stored = con.execute("select pdf,public_pdf from attachments where id=?", (att_id,)).fetchone()
            if (state != expected_state or state is None or state["decision"] != decision
                    or state["reviewed_by"] is not None or state["revision"] != expected_revision
                    or learning._snapshot(con)[1] != expected_revision
                    or stored is None or stored["pdf"] != pdf or stored["public_pdf"] is not None):
                progress(job, STEP_CLEARANCE, "error", "A newer decision or rule check takes precedence")
                why = "A newer decision or rule check takes precedence."
                if state is not None:
                    new = state["decision"]
                return
            con.execute("update attachments set clearance=?, decision=?, public_pdf=coalesce(?, public_pdf),"
                        " manifest=coalesce(?, manifest), procurement_pdf=? where id=?",
                        (json.dumps(plan), new, candidate.pdf if candidate_clear else None,
                         json.dumps(candidate.manifest) if candidate_clear else None,
                         procurement.pdf if procurement else None, att_id))
        events.log("clearance", purchase["office"], purchase["id"], att_id, filename, new,
                   sorted({r["category"] for r in public.get("remove", [])}) + [public.get("review", "error").lower()],
                   "guild-clearance", result.get("latency_ms", 0))
    except Exception:
        progress(job, STEP_CLEARANCE, "error", "Clearance failed; file stays private")
    finally:
        background_done(att_id)
        if job is not None:
            activity.finish(job, decision=new, why=why, agent_url=url, done=True)


def verify_in_background(att_id, purchase, filename, candidate, expected_decision, expected_revision,
                         expected_state, expected_digest, job=None) -> None:
    """Publish only the checked candidate, without replacing a newer staff/policy decision."""
    activity.bind(job)
    try:
        candidate_pdf = bytes(candidate.pdf)
        active, candidate_revision = learning.snapshot()
        if (candidate.verified is not True or candidate_revision != expected_revision
                or hashlib.sha256(candidate_pdf).hexdigest() != expected_digest):
            progress(job, STEP_VERIFY, "error", "Candidate or rules changed; publication remains restricted")
            return
        checked = scan(candidate_pdf)
        found = list(checked.findings) + learning.apply(checked.pages, active)
        complete = (bool(checked.pages) and not checked.coverage_issues
                    and all(p.text.strip() and not p.coverage_issues and not p.has_images
                            and not p.image and p.source == "text" for p in checked.pages))
        if not complete or any(f.severity in {"block", "review"} for f in found):
            progress(job, STEP_VERIFY, "error", "Candidate still needs review under the current rules")
            if job is not None:
                activity.finish(job, why="Current checks did not clear the candidate copy.")
            return
        # Use text extracted from the exact candidate bytes, not a cached text field.
        result = agent.verify("\n\n".join(p.text for p in checked.pages), candidate.manifest)
        new = "cleaned" if result["verdict"] == "PASS" else expected_decision
        with db() as con:
            con.execute("BEGIN IMMEDIATE")
            state = verifier_state(con, att_id)
            stored = con.execute("select public_pdf from attachments where id=?", (att_id,)).fetchone()
            # Reuse the engine's revision calculation inside this same write transaction.
            # This closes the gap between testing currentness and updating the decision.
            if (state != expected_state or state is None or state["decision"] != expected_decision
                    or state["reviewed_by"] is not None or state["revision"] != expected_revision
                    or learning._snapshot(con)[1] != expected_revision
                    or stored is None or stored["public_pdf"] != candidate_pdf):
                progress(job, STEP_VERIFY, "error", "A newer decision or rule check takes precedence")
                return
            con.execute("update attachments set verifier=?, decision=? where id=?",
                        (json.dumps(result), new, att_id))
        events.log("verifier", purchase["office"], purchase["id"], att_id, filename, new,
                   [result["verdict"].lower()], "guild-verifier", result.get("latency_ms", 0))
        progress(job, STEP_VERIFY, "done" if result["verdict"] == "PASS" else "error",
                 {"PASS": "Agrees: nothing identifies a person", "FAIL": result["text"][:80]}.get(result["verdict"], "Unavailable"))
        if job is not None:
            activity.finish(job, decision=new, agent_url=result.get("url", ""),
                            why=("The checked cleaned copy was cleared for publication." if new == "cleaned"
                                 else "The verifier did not clear the copy. Its existing restriction remains."))
    except Exception:
        progress(job, STEP_VERIFY, "error", "Verifier unavailable; file stays private")
    finally:
        background_done(att_id)
        if job is not None:
            activity.finish(job, done=True)


def brief_in_background(att_id, purchase, filename, decision, reasons, findings, job=None) -> None:
    activity.bind(job)
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
        background_done(att_id)
        if job is not None:
            activity.finish(job, done=True)


def create_purchase(office: str, procedure: str, item: str, amount: float | None, actor: str = "office", intake_details: list | None = None) -> dict:
    with db() as con:
        cur = con.execute(
            "insert into purchases (office, procedure, item, amount, created_at, intake_details) values (?,?,?,?,?,?)",
            (office, procedure, item, amount, time.time(), json.dumps(intake_details) if intake_details is not None else None))
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
    activity.bind(job)
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
        activity.bind(None)
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
    history = events.history()  # once per page load, never from the /api/activity poll
    total = (history or {}).get("total") or None
    return page(request, "live.html", offices=OFFICES, user=user, history_total=total, autonomous=autonomous())


@app.get("/documents/sample.pdf")
def sample_pdf(user: str = Depends(staff)):
    return pdf_response((FIXTURES / "fictional_patient.pdf").read_bytes(), "fictional-patient-attachment.pdf")


@app.post("/documents/upload")
async def document_upload(request: Request, files: list[UploadFile] = File(...), user: str = Depends(staff)):
    uploads = await validated_uploads(files)
    hints = intake.details(uploads)
    reserve_live(len(uploads))
    try:
        purchase = create_purchase("Unassigned", "UPLOAD-" + secrets.token_hex(6).upper(),
                                   "Uploaded documents", None, actor=user, intake_details=hints)
    except Exception:
        for _ in uploads:
            LIVE_CAPACITY.release()
        raise
    queue_live(purchase, "Uploaded documents", uploads, user)
    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse({"purchase_id": purchase["id"], "location": "/live"}, status_code=202,
                            headers={"Cache-Control": "no-store"})
    return RedirectResponse("/live", status_code=303)


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
    if activity.running():
        return PlainTextResponse("A demo run is still in progress. Wait for it to finish.", status_code=409)
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
        con.execute(senso_context.ATTACHMENT_SCHEMA.strip())
        con.execute("delete from learning_checks")
        con.execute("delete from attachment_senso")  # ids are reused after reset
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
    with db() as con:
        finished = con.execute("select count(*) from attachments where decision in ('public','cleaned','withheld')"
                               " and reviewed_by is null").fetchone()[0]
    autonomy = {"enabled": autonomous(), "finished": finished, "total": len(rows)}
    return JSONResponse({"jobs": jobs, "counts": counts, "waiting": waiting, "autonomy": autonomy,
                         "feed": activity.feed(100)},
                        headers={"Cache-Control": "no-store"})


def workspace_snapshot():
    """Bounded operational metadata; publication counts require a current check."""
    with db() as con:
        con.execute("BEGIN")
        states = con.execute("select id,decision from attachments").fetchall()
        recent = con.execute(
            "select a.id,a.purchase_id,a.filename,p.office,p.procedure,a.decision,a.created_at "
            "from attachments a left join purchases p on p.id=a.purchase_id "
            "order by a.created_at desc,a.id desc limit 100"
        ).fetchall()
    current = {row["id"]: learning.current(row["id"]) for row in states}
    counts = {"published": 0, "review": 0, "blocked": 0, "stale": 0, "total": len(states)}
    for row in states:
        counts["published"] += row["decision"] in VISIBLE and current[row["id"]]
        counts["review"] += row["decision"] == HOLD
        counts["blocked"] += row["decision"] == WITHHELD
        counts["stale"] += not current[row["id"]]
    files = [{**dict(row), "current": current[row["id"]]} for row in recent]
    return {"counts": counts, "files": files}


@app.get("/api/workspace")
def api_workspace(user: str = Depends(staff)):
    return JSONResponse(workspace_snapshot(), headers={"Cache-Control": "no-store"})


@app.get("/exposures")
def exposures(request: Request, user: str = Depends(staff)):
    from .exposure_data import COMPARISON_NOTE, EXPOSURES, RESEARCH_WINDOW, REVIEWED_AT
    return page(request, "exposures.html", user=user,
                companies=[row for row in EXPOSURES if row["entity_type"] == "company"],
                public_bodies=[row for row in EXPOSURES if row["entity_type"] == "public_body"],
                research_window=RESEARCH_WINDOW, reviewed_at=REVIEWED_AT, comparison_note=COMPARISON_NOTE)


@app.get("/")
def home(request: Request, user: str = Depends(staff)):
    return page(request, "home.html", user=user, workspace=workspace_snapshot())


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
                senso=senso_context.citations(a["id"] for a in atts),
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
        restricted = [a for a in con.execute(
            "select a.*, p.office, p.procedure, p.item from attachments a join purchases p on p.id=a.purchase_id"
            " where a.decision=? and a.reviewed_by is null order by a.id desc", (WITHHELD,)).fetchall()
            if releasable(a["findings"])]
    return page(request, "review.html", held=held, done=done, user=user, restricted=restricted,
                stale_ids={a["id"] for a in [*held, *restricted] if not learning.current(a["id"])})


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


def releasable(findings_json: str | None) -> bool:
    """Only an automatic restriction can be undone by a person. A deterministic block never can."""
    try:
        findings = [f for f in json.loads(findings_json or "[]") if isinstance(f, dict)]
    except (TypeError, ValueError):
        return False
    return (any(f.get("kind") == "autopilot_restricted" for f in findings)
            and not any(f.get("severity") == "block" for f in findings))


@app.post("/review/{att_id}/release")
def review_release(att_id: int, action: str = Form(...), note: str = Form(""), user: str = Depends(staff)):
    """Post-hoc audit of an automatic restriction: release it, or confirm it stays private."""
    if action not in ("release", "keep"):
        raise HTTPException(400, "A valid review action is required.")
    if not note.strip() or len(note.strip()) > MAX_REVIEW_NOTE:
        raise HTTPException(400, f"Explain the decision in 1–{MAX_REVIEW_NOTE} characters.")
    if action == "release" and not learning.current(att_id):
        raise HTTPException(409, "Recheck this file against the current rules before releasing it.")
    new = "approved" if action == "release" else WITHHELD
    with db() as con:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute("select a.*, p.office from attachments a join purchases p on p.id=a.purchase_id"
                          " where a.id=? and a.decision=? and a.reviewed_by is null", (att_id, WITHHELD)).fetchone()
        if not row or not releasable(row["findings"]):
            raise HTTPException(409, "Only an automatic restriction can be released.")
        updated = con.execute("update attachments set decision=?, reviewed_by=?, reviewed_at=?, review_note=?"
                              " where id=? and decision=? and reviewed_by is null",
                              (new, user, time.time(), note.strip(), att_id, WITHHELD))
        if updated.rowcount != 1:
            raise HTTPException(409, "Only an automatic restriction can be released.")
    events.log("released" if action == "release" else "kept_private", row["office"], row["purchase_id"],
               att_id, row["filename"], new, ["autopilot_restricted"], user, 0)
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
            slot["files"].append({"id": a["id"], "cleaned": a["cleaned"],
                                  "public_name": public_filename(a["purchase_id"], a["id"])})
        elif a["decision"] == "hold" or a["decision"] in VISIBLE:
            slot["pending"] += 1
        else:
            slot["kept"] += 1
    return page(request, "public.html", purchases=purchases, by_purchase=by_purchase, autonomous=autonomous())


@app.api_route("/public/file/{att_id}", methods=["GET", "HEAD"])
def public_file(att_id: int):
    """The enforcement point. Checked on every request, not at upload time only."""
    with db() as con:
        row = con.execute("select purchase_id, pdf, public_pdf, decision from attachments where id=?",
                          (att_id,)).fetchone()
    if not row or row["decision"] not in VISIBLE or not learning.current(att_id):
        raise HTTPException(404, headers={"Cache-Control": "no-store"})
    if row["decision"] == "cleaned" and not row["public_pdf"]:
        # "cleaned" promises a sanitized copy; never fall back to the original.
        raise HTTPException(404, headers={"Cache-Control": "no-store"})
    # When a cleaned copy exists, it is the only version that can ever be public.
    return pdf_response(row["public_pdf"] or row["pdf"], public_filename(row["purchase_id"], att_id))


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


@app.get("/internal/procurement/{att_id}")
def internal_procurement(att_id: int, user: str = Depends(staff)):
    """Staff view of the procurement copy: specs, quantities, prices; no patient identity."""
    with db() as con:
        row = con.execute("select filename, procurement_pdf from attachments where id=?", (att_id,)).fetchone()
    if not row or not row["procurement_pdf"]:
        raise HTTPException(404, headers={"Cache-Control": "no-store"})
    return pdf_response(row["procurement_pdf"], row["filename"])


@app.get("/dashboard")
def dashboard(request: Request, user: str = Depends(staff)):
    return page(request, "dashboard.html", s=events.stats(), h=events.history())


@app.get("/api/rules")
def api_rules():
    return RULES


@app.get("/guidelines")
def guidelines(request: Request):
    return page(request, "guidelines.html", guidelines=model_guidelines())


@app.get("/api/guidelines")
def api_guidelines():
    return model_guidelines()


@app.get("/api/senso/status")
def api_senso_status(user: str = Depends(staff)):
    return JSONResponse(senso_context.status(), headers={"Cache-Control": "no-store"})


@app.post("/learning/senso/sync")
def sync_senso(user: str = Depends(staff)):
    try:
        senso_context.sync()
    except ValueError as exc:
        raise HTTPException(502, str(exc)) from None
    events.log("senso_guidelines_synced", "Learning library", 0, actor=user)
    return RedirectResponse("/learning", status_code=303)


@app.post("/learning/senso/refresh")
def refresh_senso(user: str = Depends(staff)):
    try:
        senso_context.refresh()
    except ValueError as exc:
        raise HTTPException(502, str(exc)) from None
    return RedirectResponse("/learning", status_code=303)


@app.get("/api/pi/status")
def api_pi_status(user: str = Depends(staff)):
    # Pi Security is not connected; this reports why and what access is needed.
    return pi_context.status()


# Incident evidence generates candidates. Only reviewed, tested rules affect PDFs.
from .learning_sources import CASES
from .learning_proposer import UNVERIFIED, propose
from .skill_export import render_skill, render_proposal


def learning_rule(rule_id: int) -> dict:
    rule = learning.get_rule(rule_id)
    if not rule:
        raise HTTPException(404, "Rule not found.")
    context = senso_context.rule_context(rule_id)
    if context:
        rule["context"] = context
    return rule


def case_source(case: dict) -> dict:
    return {k: case[k] for k in ("title", "url", "evidence_status", "summary")}


def case_rules(rules: list[dict]) -> dict:
    """Map each built-in case id to its newest non-retired rule id."""
    found = {}
    for case in CASES:
        source = learning._source(case_source(case))
        found[case["id"]] = next((r["id"] for r in sorted(rules, key=lambda r: -r["id"])
                                  if r["status"] != "retired" and r["source"] == source), None)
    return found


@app.get("/learning")
def learning_home(request: Request, lead: str = "", user: str = Depends(staff)):
    rules = learning.list_rules()
    selected = incident_discovery.get_lead(lead) if lead else None
    return page(request, "learning.html", cases=CASES, rules=rules, case_rules=case_rules(rules),
                active_count=sum(r["status"] == "active" for r in rules),
                pending_count=learning.pending_count(), senso=senso_context.status(), user=user,
                leads=incident_discovery.list_leads(), source_prefill=incident_discovery.source_prefill(selected) if selected else None)


@app.post("/learning/discover")
def discover_incidents(user: str = Depends(staff)):
    try:
        incident_discovery.discover()
    except ValueError as exc:
        raise HTTPException(502, str(exc)) from None
    events.log("incident_reporting_discovered", "Learning library", 0, actor=user)
    return RedirectResponse("/learning#news-leads", status_code=303)


@app.post("/learning/from-case/{case_id}")
def learn_from_case(case_id: str, user: str = Depends(staff)):
    case = next((c for c in CASES if c["id"] == case_id), None)
    if case is None:
        raise HTTPException(404, "Source case not found.")
    existing = case_rules(learning.list_rules())[case_id]
    if existing is not None:
        return RedirectResponse(f"/learning/rules/{existing}", status_code=303)
    source = case_source(case)
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
                      use_senso: bool = Form(False),
                      user: str = Depends(staff)):
    if evidence_status not in {"reported", "acknowledged", "alleged", "unknown"}:
        raise HTTPException(400, "Choose a valid source evidence status.")
    source = {"title": title, "url": url, "evidence_status": UNVERIFIED,
              "summary": f"Submitter describes evidence as: {evidence_status}.\n\n{summary}"}
    try:
        context = senso_context.retrieve(title) if use_senso else None
        spec, generator = propose(source, context=context) if context else propose(source)
        ident = learning.create_candidate(spec, source, user, generator=generator, context=context)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    events.log("rule_proposed", "Learning library", 0, actor=user)
    return RedirectResponse(f"/learning/rules/{ident}", status_code=303)


@app.get("/learning/rules/{rule_id}")
def learning_detail(request: Request, rule_id: int, user: str = Depends(staff)):
    return page(request, "learning_rule.html", rule=learning_rule(rule_id),
                pending_count=learning.pending_count(), context=senso_context.rule_context(rule_id), user=user)


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
    if autonomous():
        recheck_all("autopilot")
    return RedirectResponse(f"/learning/rules/{rule_id}", status_code=303)


@app.post("/learning/rules/{rule_id}/retire")
def retire_learning_rule(rule_id: int, digest: str = Form(...), user: str = Depends(staff)):
    learning_rule(rule_id)
    try:
        learning.deactivate(rule_id, digest, user)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    events.log("rule_retired", "Learning library", 0, actor=user)
    if autonomous():
        recheck_all("autopilot")
    return RedirectResponse(f"/learning/rules/{rule_id}", status_code=303)


@app.post("/learning/rescan")
def rescan_learning_rules(user: str = Depends(staff)):
    result = recheck_all(user)
    if result["error"]:
        raise HTTPException(409, result["error"])
    return RedirectResponse("/learning", status_code=303)


def recheck_all(actor: str) -> dict:
    """Recheck every stored file against the current rules. Only restricts, never releases."""
    from dataclasses import asdict
    result = {"checked": 0, "restricted": 0, "settled": 0, "error": None}
    active, checked_revision = learning.snapshot()
    with db() as con:
        attachments = con.execute("select * from attachments order by id").fetchall()
    for attachment in attachments:
        # Recheck the bytes /public/file would actually serve: a published cleaned copy
        # replaces the original, so new rules must be applied to that copy.
        served = attachment["public_pdf"] if attachment["decision"] in VISIBLE and attachment["public_pdf"] else attachment["pdf"]
        scanned = scan(served)
        learned = learning.apply(scanned.pages, active)
        found = list(scanned.findings) + learned
        incomplete = []
        if (not scanned.pages or scanned.coverage_issues
                or any(p.coverage_issues for p in scanned.pages)):
            incomplete.append(Finding("incomplete_recheck", "Recheck coverage is incomplete", "",
                                      0, "review", "unreadable"))
        found += incomplete
        decision = attachment["decision"]
        # A cleaned copy already passed the independent verifier with its built-in
        # review-level findings; only learned rules or lost coverage reopen it.
        review_triggers = learned + incomplete if decision == "cleaned" else found
        if any(f.severity == "block" for f in found):
            decision = WITHHELD
        elif any(f.severity == "review" for f in review_triggers) and decision in VISIBLE:
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
            strictness = {"public": 0, "approved": 0, "cleaned": 0, "hold": 1, "withheld": 2}
            if strictness.get(current_row["decision"], 2) >= strictness.get(decision, 2):
                decision = current_row["decision"]
            con.execute("update attachments set decision=?,findings=?,reasons=? where id=?",
                        (decision, json.dumps(merged), json.dumps(reasons), attachment["id"]))
        try:
            learning.record_check(attachment["id"], checked_revision)
        except ValueError:
            result["error"] = ("Rules changed during the recheck. Unchecked files remain unavailable. "
                               "Run the recheck again.")
            break
        result["checked"] += 1
        result["restricted"] += decision != attachment["decision"]
        events.log("rule_recheck", "Learning library", attachment["purchase_id"],
                   attachment["id"], attachment["filename"], decision,
                   sorted({f.kind for f in found}), actor)
        if decision == HOLD:
            result["settled"] += settle(attachment["id"])
    return result


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
