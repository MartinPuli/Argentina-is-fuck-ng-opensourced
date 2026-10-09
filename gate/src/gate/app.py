"""Web app: a fictional PAMI with an internal side and a public side.

Internal (staff password): offices upload purchases, reviewers clear held files.
Public: the purchasing portal. It serves an attachment only if the gate cleared it.
"""

import hashlib
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
from fastapi.responses import PlainTextResponse, RedirectResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from . import agent, llm, learning  # noqa: E402
from .detect import Finding, scan  # noqa: E402
from .policy import PUBLIC, WITHHELD, decide  # noqa: E402
from .rules import RULES  # noqa: E402
from .store import Events, db  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures" / "pdfs"
OFFICES = ["UGL XXIII Jujuy", "UGL XXX Chivilcoy", "UGL XIX Misiones", "UGL VI Capital Federal"]
VISIBLE = ("public", "approved")
MAX_FILES = 8
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_PDF_PAGES = 50
MAX_REVIEW_NOTE = 2000

app = FastAPI(title="Publication Gate")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.filters["money"] = lambda v: f"$ {v:,.0f}".replace(",", ".")
templates.env.filters["fromjson"] = lambda v: json.loads(v) if v else None
templates.env.globals["RULES"] = RULES
events = Events()
basic = HTTPBasic(auto_error=False)


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


def evaluate(pdf: bytes) -> tuple:
    started = time.perf_counter()
    active, rules_revision = learning.snapshot()
    result = scan(pdf)
    result.findings.extend(learning.apply(result.pages, active))
    model = llm.review("\n\n".join(p.text for p in result.pages))
    images = [llm.review_image(p.image) if p.image else None for p in result.pages]
    decision, reasons, findings = decide(result, model, images)
    return model, decision, reasons, findings, (time.perf_counter() - started) * 1000, rules_revision


def gate_files(purchase: dict, files: list[tuple[str, bytes]]) -> None:
    """Check all attachments of a purchase in parallel, then store them in order."""
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda f: evaluate(f[1]), files))
    for (filename, pdf), evaluated in zip(files, results):
        store_attachment(purchase, filename, pdf, *evaluated)


def store_attachment(purchase: dict, filename: str, pdf: bytes, model, decision, reasons,
                     findings, latency, rules_revision=None) -> int:
    """Store one checked file and log the decision."""
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
    if decision != PUBLIC and agent.configured():
        threading.Thread(target=brief_in_background, args=(att_id, purchase, filename, decision,
                                                           reasons, findings), daemon=True).start()
    return att_id


def brief_in_background(att_id, purchase, filename, decision, reasons, findings) -> None:
    brief = agent.brief(purchase, filename, decision, reasons, findings)
    with db() as con:
        con.execute("update attachments set agent=? where id=?", (json.dumps(brief), att_id))
    events.log("agent_brief", purchase["office"], purchase["id"], att_id, filename, decision,
               [], "guild-agent", brief.get("latency_ms", 0))


def create_purchase(office: str, procedure: str, item: str, amount: float) -> dict:
    with db() as con:
        cur = con.execute(
            "insert into purchases (office, procedure, item, amount, created_at) values (?,?,?,?,?)",
            (office, procedure, item, amount, time.time()))
        purchase = {"id": cur.lastrowid, "office": office}
    events.log("submitted", office, purchase["id"], actor="office")
    return purchase


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
    purchase = create_purchase(office, procedure, item, amount)
    gate_files(purchase, uploads)
    return RedirectResponse(f"/purchase/{purchase['id']}", status_code=303)


@app.post("/demo/seed")
def demo_seed(user: str = Depends(staff)):
    first = None
    for p in json.loads((FIXTURES / "purchases.json").read_text()):
        purchase = create_purchase(p["office"], p["procedure"], p["item"], p["amount"])
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
        atts = con.execute("select id, purchase_id, filename, decision from attachments").fetchall()
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
        row = con.execute("select filename, pdf, decision from attachments where id=?", (att_id,)).fetchone()
    if not row or row["decision"] not in VISIBLE or not learning.current(att_id):
        raise HTTPException(404, headers={"Cache-Control": "no-store"})
    return pdf_response(row["pdf"], row["filename"])


@app.get("/internal/file/{att_id}")
def internal_file(att_id: int, user: str = Depends(staff)):
    with db() as con:
        row = con.execute("select filename, pdf from attachments where id=?", (att_id,)).fetchone()
    if not row:
        raise HTTPException(404, headers={"Cache-Control": "no-store"})
    return pdf_response(row["pdf"], row["filename"])


@app.get("/dashboard")
def dashboard(request: Request, user: str = Depends(staff)):
    return page(request, "dashboard.html", s=events.stats())


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
