"""Web app: a fictional PAMI with an internal side and a public side.

Internal (staff password): offices upload purchases, reviewers clear held files.
Public: the purchasing portal. It serves an attachment only if the gate cleared it.
"""

import hashlib
import json
import os
import secrets
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

load_dotenv(Path(__file__).resolve().parents[3] / ".env")
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from . import agent, llm  # noqa: E402
from .detect import scan  # noqa: E402
from .policy import PUBLIC, WITHHELD, decide  # noqa: E402
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


def gate_attachment(purchase: dict, filename: str, pdf: bytes) -> int:
    """Run one file through the gate, store it, log the decision."""
    started = time.perf_counter()
    result = scan(pdf)
    model = llm.review("\n\n".join(p.text for p in result.pages))
    decision, reasons, findings = decide(result, model)
    latency = (time.perf_counter() - started) * 1000
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
    purchase = create_purchase(office, procedure, item, amount)
    for f in files:
        data = await f.read()
        if data:
            gate_attachment(purchase, f.filename or "adjunto.pdf", data)
    return RedirectResponse(f"/purchase/{purchase['id']}", status_code=303)


@app.post("/demo/seed")
def demo_seed(user: str = Depends(staff)):
    last = None
    for p in json.loads((FIXTURES / "purchases.json").read_text()):
        purchase = create_purchase(p["office"], p["procedure"], p["item"], p["amount"])
        for name in p["files"]:
            gate_attachment(purchase, name, (FIXTURES / name).read_bytes())
        last = purchase["id"]
    return RedirectResponse(f"/purchase/{last - 1 if last and last > 1 else last}", status_code=303)


@app.get("/purchase/{pid}")
def purchase_view(request: Request, pid: int, user: str = Depends(staff)):
    with db() as con:
        purchase = con.execute("select * from purchases where id=?", (pid,)).fetchone()
        if not purchase:
            raise HTTPException(404)
        atts = con.execute("select * from attachments where purchase_id=? order by id", (pid,)).fetchall()
    return page(request, "purchase.html", purchase=purchase, atts=atts)


@app.get("/review")
def review_queue(request: Request, user: str = Depends(staff)):
    with db() as con:
        held = con.execute(
            "select a.*, p.office, p.procedure, p.item from attachments a join purchases p "
            "on p.id=a.purchase_id where a.decision='hold' order by a.id").fetchall()
        done = con.execute(
            "select a.*, p.office from attachments a join purchases p on p.id=a.purchase_id "
            "where a.reviewed_by is not null order by a.reviewed_at desc limit 10").fetchall()
    return page(request, "review.html", held=held, done=done, user=user)


@app.post("/review/{att_id}")
def review_decide(att_id: int, action: str = Form(...), reviewer: str = Form(...),
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
    return RedirectResponse("/review", status_code=303)


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
