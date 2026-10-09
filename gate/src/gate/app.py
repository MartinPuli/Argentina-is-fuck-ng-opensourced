"""Web app: a staff side and a public side.

Staff: live view of the agent, decisions waiting for a person, upload, audit log.
Public: the purchasing portal. It serves an attachment only if the gate cleared it.
"""

import hashlib
import json
import os
import secrets
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import PlainTextResponse, RedirectResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from . import activity, agent, llm  # noqa: E402
from .detect import scan  # noqa: E402
from .policy import HOLD, PUBLIC, WITHHELD, decide  # noqa: E402
from .rules import RULES  # noqa: E402
from .store import Events, db  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures" / "pdfs"
OFFICES = ["UGL XXIII Jujuy", "UGL XXX Chivilcoy", "UGL XIX Misiones", "UGL VI Capital Federal"]
VISIBLE = ("public", "approved")

app = FastAPI(title="Publication Gate")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.filters["money"] = lambda v: f"$ {v:,.0f}".replace(",", ".")
templates.env.filters["fromjson"] = lambda v: json.loads(v) if v else None
templates.env.globals["RULES"] = RULES
events = Events()
basic = HTTPBasic(auto_error=False)


@app.middleware("http")
async def same_origin_posts(request: Request, call_next):
    """Reject cross-site form posts (CSRF).

    Found by Semgrep: without this, any web page could make a reviewer's browser
    submit "Approve for public" and publish a held medical file.
    """
    if request.method == "POST":
        source = request.headers.get("origin") or request.headers.get("referer") or ""
        host = request.headers.get("host", "")
        if urlsplit(source).netloc != host:
            return PlainTextResponse("cross-site request blocked", status_code=403)
    return await call_next(request)


def staff(creds: HTTPBasicCredentials | None = Depends(basic)) -> str:
    password = os.getenv("GATE_STAFF_PASSWORD")
    if not password:
        return creds.username if creds else "staff"
    if creds and secrets.compare_digest(creds.password, password):
        return creds.username
    raise HTTPException(401, headers={"WWW-Authenticate": 'Basic realm="PAMI internal"'})


def page(request: Request, name: str, **ctx) -> Response:
    ctx.setdefault("llm_on", llm.configured())
    ctx.setdefault("agent_on", agent.configured())
    ctx.setdefault("events_backend", events.backend)
    return templates.TemplateResponse(request, name, ctx)


STEP_READ = "Read"
STEP_SCAN = "Find IDs"
STEP_AI = "AkashML AI"
STEP_VISION = "AkashML vision"
STEP_DECIDE = "Decide"
STEP_BRIEF = "Guild agent note"
SHORT = {"CUIL of a private person": "CUIL", "National ID (DNI) number": "DNI", "PAMI affiliate number": "affiliate no.",
         "Date of birth": "birth date", "Home address": "address", "Image or copy of an identity document": "ID copy",
         "Disability certificate": "disability cert.", "Diagnosis code (ICD-10)": "diagnosis", "Clinical language": "medical terms"}
LABEL = {"public": "Published", "approved": "Published", "hold": "Needs you", "withheld": "Blocked"}


def evaluate(pdf: bytes, job: dict) -> tuple:
    started = time.perf_counter()
    activity.step(job, STEP_READ, "running")
    result = scan(pdf)
    pages = len(result.pages)
    activity.step(job, STEP_READ, "done", f"{pages} page{'s' * (pages != 1)}" + (", scanned (OCR)" if result.ocr_used else ""))
    hits = sorted({f.label for f in result.findings if f.severity != "info"})
    activity.step(job, STEP_SCAN, "done", ", ".join(hits) if hits else "nothing found")

    if llm.configured():
        activity.step(job, STEP_AI, "running")
        model = llm.review("\n\n".join(p.text for p in result.pages))
        risk = (model or {}).get("reidentification_risk")
        activity.step(job, STEP_AI, "error" if "error" in (model or {}) else "done",
                      "unavailable" if "error" in (model or {}) else f"risk: {risk}")
    else:
        model = None
        activity.step(job, STEP_AI, "skipped", "off")

    images = []
    if any(p.image for p in result.pages) and llm.configured():
        activity.step(job, STEP_VISION, "running")
        images = [llm.review_image(p.image) if p.image else None for p in result.pages]
        kinds = [str(i.get("kind", "")) for i in images if i and "error" not in i]
        activity.step(job, STEP_VISION, "done", "; ".join(kinds)[:140] or "unavailable")

    decision, reasons, findings = decide(result, model, images)
    activity.step(job, STEP_DECIDE, "done", LABEL[decision])
    kinds = {f["kind"] for f in findings}
    if decision == WITHHELD:
        why = ", ".join(SHORT.get(h, h) for h in hits[:3])
    elif "model_context" in kinds:
        why = "identifies a patient without a name"
    elif "unreadable_scan" in kinds or "model_image" in kinds:
        why = "unreadable image"
    elif decision == HOLD:
        why = "medical wording"
    else:
        why = "clean"
    activity.finish(job, why=why)
    return model, decision, reasons, findings, (time.perf_counter() - started) * 1000


def plan_steps(pdf_is_scan: bool = True) -> list[str]:
    return [STEP_READ, STEP_SCAN, STEP_AI, STEP_DECIDE]


def gate_files(purchase: dict, item: str, files: list[tuple[str, bytes]]) -> None:
    """Queue every attachment in the live view, then check them in the background."""
    jobs = [activity.start(purchase, item, name, plan_steps()) for name, _ in files]

    def run() -> None:
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda pair: safe_evaluate(*pair), zip([f[1] for f in files], jobs)))
        for (filename, pdf), job, evaluated in zip(files, jobs, results):
            if evaluated:
                store_attachment(purchase, filename, pdf, job, *evaluated)

    threading.Thread(target=run, daemon=True).start()


def safe_evaluate(pdf: bytes, job: dict):
    try:
        return evaluate(pdf, job)
    except Exception as exc:  # show the failure instead of hanging the live view
        activity.step(job, STEP_DECIDE, "error", f"{type(exc).__name__}")
        activity.finish(job, done=True, decision="error")
        return None


def store_attachment(purchase: dict, filename: str, pdf: bytes, job: dict, model, decision,
                     reasons, findings, latency) -> int:
    """Store one checked file, log the decision, ask the Guild agent for a note."""
    with db() as con:
        cur = con.execute(
            "insert into attachments (purchase_id, filename, sha256, pdf, decision, reasons,"
            " findings, model, created_at) values (?,?,?,?,?,?,?,?,?)",
            (purchase["id"], filename, hashlib.sha256(pdf).hexdigest(), pdf, decision,
             json.dumps(reasons), json.dumps(findings), json.dumps(model), time.time()),
        )
        att_id = cur.lastrowid
    events.log("decision", purchase["office"], purchase["id"], att_id, filename, decision,
               sorted({f["kind"] for f in findings}), "gate", latency)
    activity.finish(job, attachment_id=att_id, decision=decision)
    if decision != PUBLIC and agent.configured():
        activity.step(job, STEP_BRIEF, "running")
        threading.Thread(target=brief_in_background, args=(att_id, purchase, filename, decision,
                                                           reasons, findings, job), daemon=True).start()
    else:
        activity.finish(job, done=True)
    return att_id


def brief_in_background(att_id, purchase, filename, decision, reasons, findings, job) -> None:
    brief = agent.brief(purchase, filename, decision, reasons, findings)
    with db() as con:
        con.execute("update attachments set agent=? where id=?", (json.dumps(brief), att_id))
    events.log("agent_brief", purchase["office"], purchase["id"], att_id, filename, decision,
               [], "guild-agent", brief.get("latency_ms", 0))
    activity.step(job, STEP_BRIEF, "error" if "error" in brief else "done",
                  "unavailable" if "error" in brief else "ready")
    activity.finish(job, done=True, agent_url=brief.get("url", ""))


def create_purchase(office: str, procedure: str, item: str, amount: float) -> dict:
    with db() as con:
        cur = con.execute(
            "insert into purchases (office, procedure, item, amount, created_at) values (?,?,?,?,?)",
            (office, procedure, item, amount, time.time()))
        purchase = {"id": cur.lastrowid, "office": office}
    events.log("submitted", office, purchase["id"], actor="office")
    return purchase


@app.get("/")
def home(request: Request, user: str = Depends(staff)):
    return page(request, "home.html", offices=OFFICES, user=user)


@app.get("/office")
def office_form():
    return RedirectResponse("/", status_code=303)


@app.post("/office")
async def office_submit(office: str = Form(...), procedure: str = Form(...), item: str = Form(...),
                        amount: float = Form(...), files: list[UploadFile] = File(...),
                        user: str = Depends(staff)):
    purchase = create_purchase(office, procedure, item, amount)
    uploads = [(f.filename or "adjunto.pdf", await f.read()) for f in files]
    gate_files(purchase, item, [u for u in uploads if u[1]])
    return RedirectResponse("/", status_code=303)


@app.post("/demo/seed")
def demo_seed(user: str = Depends(staff)):
    for p in json.loads((FIXTURES / "purchases.json").read_text()):
        purchase = create_purchase(p["office"], p["procedure"], p["item"], p["amount"])
        gate_files(purchase, p["item"], [(name, (FIXTURES / name).read_bytes()) for name in p["files"]])
    return RedirectResponse("/", status_code=303)


@app.get("/purchase/{pid}")
def purchase_view(request: Request, pid: int, user: str = Depends(staff)):
    with db() as con:
        purchase = con.execute("select * from purchases where id=?", (pid,)).fetchone()
        if not purchase:
            raise HTTPException(404)
        atts = con.execute("select * from attachments where purchase_id=? order by id", (pid,)).fetchall()
    return page(request, "purchase.html", purchase=purchase, atts=atts)


@app.get("/review")
def review_queue():
    return RedirectResponse("/", status_code=303)


@app.get("/api/activity")
def api_activity(user: str = Depends(staff)):
    """Everything the live view needs, in one poll."""
    with db() as con:
        counts = dict(con.execute("select decision, count(*) from attachments group by decision").fetchall())
        waiting = con.execute(
            "select a.id, a.filename, a.findings, a.agent, p.office, p.item, p.id as pid "
            "from attachments a join purchases p on p.id=a.purchase_id "
            "where a.decision='hold' order by a.id").fetchall()
    return {
        "jobs": activity.snapshot(),
        "counts": {"published": counts.get("public", 0) + counts.get("approved", 0),
                   "waiting": counts.get("hold", 0), "blocked": counts.get("withheld", 0)},
        "waiting": [{
            "id": w["id"], "file": w["filename"], "office": w["office"], "item": w["item"], "pid": w["pid"],
            "why": sorted({SHORT.get(f["label"], f["label"]) for f in json.loads(w["findings"] or "[]")
                           if f["kind"] not in ("model_context", "unreadable_scan", "model_image")}),
            "risk": next((f["evidence"] for f in json.loads(w["findings"] or "[]") if f["kind"] == "model_context"), ""),
            "note": (json.loads(w["agent"]) or {}).get("text", "") if w["agent"] else "",
            "agent_url": (json.loads(w["agent"]) or {}).get("url", "") if w["agent"] else "",
        } for w in waiting],
    }


@app.post("/review/{att_id}")
def review_decide(att_id: int, action: str = Form(...), reviewer: str = Form("staff"),
                  note: str = Form(""), user: str = Depends(staff)):
    if action not in ("approve", "reject") or not reviewer.strip():
        raise HTTPException(400, "reviewer name and a valid action are required")
    new = "approved" if action == "approve" else WITHHELD
    with db() as con:
        row = con.execute("select a.*, p.office from attachments a join purchases p on "
                          "p.id=a.purchase_id where a.id=? and a.decision='hold'", (att_id,)).fetchone()
        if not row:
            raise HTTPException(409, "not waiting for review")
        con.execute("update attachments set decision=?, reviewed_by=?, reviewed_at=?, review_note=?"
                    " where id=?", (new, reviewer.strip(), time.time(), note.strip(), att_id))
    waited = (time.time() - row["created_at"]) * 1000
    events.log("approved" if new == "approved" else "rejected", row["office"], row["purchase_id"],
               att_id, row["filename"], new, [], reviewer.strip(), waited)
    return RedirectResponse("/", status_code=303)


@app.get("/public")
def public_portal(request: Request):
    with db() as con:
        purchases = con.execute("select * from purchases order by id desc").fetchall()
        atts = con.execute("select id, purchase_id, filename, decision from attachments").fetchall()
    by_purchase: dict[int, dict] = {}
    for a in atts:
        slot = by_purchase.setdefault(a["purchase_id"], {"files": [], "kept": 0, "pending": 0})
        if a["decision"] in VISIBLE:
            slot["files"].append(a)
        elif a["decision"] == "hold":
            slot["pending"] += 1
        else:
            slot["kept"] += 1
    return page(request, "public.html", purchases=purchases, by_purchase=by_purchase)


@app.get("/public/file/{att_id}")
def public_file(att_id: int):
    """The enforcement point. Checked on every request, not at upload time only."""
    with db() as con:
        row = con.execute("select filename, pdf, decision from attachments where id=?", (att_id,)).fetchone()
    if not row or row["decision"] not in VISIBLE:
        raise HTTPException(404)
    return Response(row["pdf"], media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{row["filename"]}"'})


@app.get("/internal/file/{att_id}")
def internal_file(att_id: int, user: str = Depends(staff)):
    with db() as con:
        row = con.execute("select filename, pdf from attachments where id=?", (att_id,)).fetchone()
    if not row:
        raise HTTPException(404)
    return Response(row["pdf"], media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{row["filename"]}"'})


@app.get("/dashboard")
def dashboard(request: Request):
    return page(request, "dashboard.html", s=events.stats())


@app.get("/api/rules")
def api_rules():
    return RULES
