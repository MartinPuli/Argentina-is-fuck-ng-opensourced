"""Publication-learning workflow through HTTP, with no live provider calls.

Plan: propose a rule from a named evidence case; require its tests and exact digest
before activation; observe exact public PDF bytes before/after the revision; check
new uploads, benign continuity, monotonic blocking, staff-only exports and CSRF.
The model's safe result is constructed solely to isolate the learned rule. This
is not evidence of model accuracy, autonomous learning or sponsor integration.
"""

import importlib
import io
import json
import zipfile
from types import SimpleNamespace

import dotenv
import pymupdf
import pytest
from fastapi.testclient import TestClient

from gate import agent, detect, llm

STAFF = ("learning-test-reviewer", "fictional-learning-test-password")
CASE_ID = "pami-private-attachments"
SAFE_TEXT = {
    "safe_for_public": True, "personal_data": False, "health_data": False,
    "reidentification_risk": "none", "reasons": [],
}
POSITIVE = (
    "Documento ficticio. Ficha asistencial individual.\n"
    "Código de paciente: DEMO-ALFA.\n"
    "Prestación asignada: visita domiciliaria."
)
BENIGN = (
    "Documento ficticio. Ficha asistencial individual: plantilla vacía.\n"
    "Prestación asignada: visita domiciliaria.\n"
    "Material público de capacitación sin identificador individual."
)
BUILTIN_BLOCK = "Documento ficticio. DNI: 31.846.275. Registro sintético para una prueba."


def pdf(text):
    with pymupdf.open() as document:
        page = document.new_page()
        page.insert_text((72, 72), text, fontsize=11)
        return document.tobytes()


@pytest.fixture
def web(monkeypatch, tmp_path):
    for var in ("AKASHML_API_KEY", "GUILD_WORKSPACE", "GUILD_AGENT", "CLICKHOUSE_HOST"):
        monkeypatch.setenv(var, "")
    monkeypatch.setenv("GATE_DB", str(tmp_path / "learning.sqlite3"))
    monkeypatch.setenv("GATE_STAFF_USERNAME", STAFF[0])
    monkeypatch.setenv("GATE_STAFF_PASSWORD", STAFF[1])
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: False)

    def unexpected_provider(*args, **kwargs):
        pytest.fail("learning HTTP tests must not invoke a live provider or OCR")

    monkeypatch.setattr(llm, "OpenAI", unexpected_provider)
    monkeypatch.setattr(agent, "configured", lambda: False)
    monkeypatch.setattr(agent, "brief", unexpected_provider)
    monkeypatch.setattr(detect.pytesseract, "image_to_string", unexpected_provider)
    monkeypatch.setattr(llm, "review", lambda _text: dict(SAFE_TEXT))
    monkeypatch.setattr(llm, "review_image", unexpected_provider)
    store = importlib.import_module("gate.store")
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "learning.sqlite3")
    app_module = importlib.import_module("gate.app")
    learning = importlib.import_module("gate.learning")
    monkeypatch.setattr(app_module, "events", store.Events())
    with TestClient(app_module.app, headers={"origin": "http://testserver"}) as client:
        client.auth = STAFF
        with TestClient(app_module.app, headers={"origin": "http://testserver"}) as anonymous:
            yield SimpleNamespace(client=client, anonymous=anonymous, app=app_module,
                                  store=store, learning=learning, monkeypatch=monkeypatch)


def upload(web, files):
    """Submit actual PDFs through the same multipart endpoint as the office UI."""
    response = web.client.post("/office", data={
        "office": web.app.OFFICES[0], "procedure": "DEMO-LEARNING",
        "item": "Fictional public equipment purchase", "amount": "1250",
    }, files=[("files", (name, body, "application/pdf")) for name, body in files.items()],
       follow_redirects=False)
    assert response.status_code == 303, response.text
    purchase_id = int(response.headers["location"].rsplit("/", 1)[-1])
    with web.store.db() as con:
        rows = con.execute("select * from attachments where purchase_id=? order by id",
                           (purchase_id,)).fetchall()
    assert {row["filename"] for row in rows} == set(files)
    return {row["filename"]: dict(row) for row in rows}


def public(web, row):
    return web.anonymous.get(f"/public/file/{row['id']}")


def propose(web):
    response = web.client.post(f"/learning/from-case/{CASE_ID}", follow_redirects=False)
    assert response.status_code == 303, response.text
    rules = web.learning.list_rules()
    assert len(rules) == 1
    rule = rules[0]
    assert rule["status"] == "draft"
    return rule


def test_case_rule_changes_real_pdf_publication_without_loosening_existing_blocks(web):
    library = web.client.get("/learning")
    assert library.status_code == 200
    assert "Your first lesson starts with a source." in library.text
    assert "AkashML is not configured." in library.text
    bodies = {"before-positive.pdf": pdf(POSITIVE), "before-benign.pdf": pdf(BENIGN),
              "before-withheld.pdf": pdf(BUILTIN_BLOCK), "before-pending.pdf": pdf(POSITIVE)}
    # Make the two old files genuinely reviewer-approved through HTTP, rather than
    # constructing approved state in the database. No text provider is involved.
    with web.monkeypatch.context() as patch:
        patch.setattr(llm, "review", lambda _text: None)
        old = upload(web, bodies)
    for name in ("before-positive.pdf", "before-benign.pdf"):
        assert old[name]["decision"] == "hold"
        response = web.client.post(f"/review/{old[name]['id']}", data={
            "action": "approve", "reviewer": "untrusted-display-name",
            "note": "Reviewed this fictional text under the earlier publication rules.",
        }, follow_redirects=False)
        assert response.status_code == 303
        assert public(web, old[name]).content == bodies[name]
    assert old["before-withheld.pdf"]["decision"] == "withheld"
    assert public(web, old["before-withheld.pdf"]).status_code == 404

    rule = propose(web)
    route = f"/learning/rules/{rule['id']}"
    library = web.client.get("/learning")
    detail = web.client.get(route)
    assert library.status_code == detail.status_code == 200
    assert rule["spec"]["title"] in library.text and 'rule-draft' in library.text
    assert "Nothing has been tested yet." in detail.text
    assert rule["digest"] in detail.text and rule["source"]["url"] in detail.text
    example = web.client.get(route + "/example/0.pdf")
    assert example.status_code == 200 and example.headers["content-type"] == "application/pdf"
    with pymupdf.open(stream=example.content, filetype="pdf") as document:
        text = " ".join(" ".join(page.get_text() for page in document).split())
    assert "FICTIONAL TEST DOCUMENT" in text
    assert " ".join(rule["spec"]["tests"][0]["text"].split()) in text
    assert web.client.get(route + "/example/999.pdf").status_code == 404
    assert web.client.post(route + "/activate", data={"digest": rule["digest"]},
                           follow_redirects=False).status_code == 400
    assert web.learning.get_rule(rule["id"])["status"] == "draft"
    tested = web.client.post(route + "/test", follow_redirects=False)
    assert tested.status_code == 303, tested.text
    rule = web.learning.get_rule(rule["id"])
    assert rule["status"] == "tested"
    library = web.client.get("/learning")
    detail = web.client.get(route)
    assert library.status_code == detail.status_code == 200
    assert 'rule-tested' in library.text
    assert "checks passed" in detail.text and "Before this rule" in detail.text
    report = rule["results"]
    assert report["passed"] is True and report["passed_count"] == report["total"]
    assert any(case["should_match"] for case in report["cases"])
    assert any(not case["should_match"] for case in report["cases"])
    assert report["candidate"]["passed"] > report["baseline"]["passed"]
    assert web.client.post(route + "/activate", data={"digest": "0" * 64},
                           follow_redirects=False).status_code == 400
    assert web.learning.get_rule(rule["id"])["status"] == "tested"
    activated = web.client.post(route + "/activate", data={"digest": rule["digest"]},
                                follow_redirects=False)
    assert activated.status_code == 303, activated.text
    assert web.learning.get_rule(rule["id"])["status"] == "active"
    library = web.client.get("/learning")
    detail = web.client.get(route)
    assert library.status_code == detail.status_code == 200
    assert 'rule-active' in library.text
    assert "The rules changed. Check existing files too." in library.text
    assert "This rule is active." in detail.text

    # A saved approval from an older rules revision cannot bypass the new gate.
    for name in ("before-positive.pdf", "before-benign.pdf"):
        response = public(web, old[name])
        assert response.status_code == 404 and response.content != bodies[name]
    portal = web.anonymous.get("/public").text
    assert "before-positive.pdf" not in portal and "before-benign.pdf" not in portal
    assert web.client.post(f"/review/{old['before-pending.pdf']['id']}", data={
        "action": "approve", "note": "Try to approve without checking the new revision.",
    }, follow_redirects=False).status_code == 409

    # New uploads have the active revision immediately. A benign counterpart
    # proves that the positive file is not denied merely by missing revision data.
    new_bodies = {"new-positive.pdf": pdf(POSITIVE), "new-benign.pdf": pdf(BENIGN)}
    new = upload(web, new_bodies)
    assert new["new-positive.pdf"]["decision"] == "hold"
    assert public(web, new["new-positive.pdf"]).status_code == 404
    allowed = public(web, new["new-benign.pdf"])
    assert allowed.status_code == 200 and allowed.content == new_bodies["new-benign.pdf"]

    rescanned = web.client.post("/learning/rescan", follow_redirects=False)
    assert rescanned.status_code == 303, rescanned.text
    assert public(web, old["before-positive.pdf"]).status_code == 404
    benign = public(web, old["before-benign.pdf"])
    assert benign.status_code == 200 and benign.content == bodies["before-benign.pdf"]
    assert public(web, old["before-withheld.pdf"]).status_code == 404
    with web.store.db() as con:
        saved = {row["filename"]: dict(row) for row in con.execute("select * from attachments")}
    assert saved["before-positive.pdf"]["decision"] == "hold"
    assert saved["before-benign.pdf"]["decision"] == "approved"
    assert saved["before-benign.pdf"]["reviewed_by"] == STAFF[0]
    assert saved["before-withheld.pdf"]["decision"] == "withheld"

    skill = web.client.get(route + "/skill.md")
    proposal = web.client.get(route + "/proposal.md")
    assert skill.status_code == proposal.status_code == 200
    assert rule["source"]["url"] in skill.text and rule["source"]["url"] in proposal.text
    assert rule["digest"] in skill.text and rule["digest"] in proposal.text
    assert report["cases"][0]["name"] in skill.text
    assert "does not install a skill, activate a rule" in skill.text
    assert "grant access to a service" in skill.text
    bundle = web.client.get(route + "/bundle.zip")
    assert bundle.status_code == 200
    with zipfile.ZipFile(io.BytesIO(bundle.content)) as archive:
        assert set(archive.namelist()) == {"SKILL.md", "PROPOSAL.md", "evidence.json"}
        assert archive.read("SKILL.md").decode() == skill.text
        assert archive.read("PROPOSAL.md").decode() == proposal.text
        evidence = json.loads(archive.read("evidence.json"))
        assert evidence["digest"] == rule["digest"]
        assert evidence["source"] == rule["source"]
        assert evidence["results"]["passed"] is True

    assert web.client.post(route + "/retire", data={"digest": "0" * 64},
                           follow_redirects=False).status_code == 400
    assert web.client.post(route + "/retire", data={"digest": rule["digest"]},
                           follow_redirects=False).status_code == 303
    assert web.learning.get_rule(rule["id"])["status"] == "retired"
    detail = web.client.get(route)
    library = web.client.get("/learning")
    assert detail.status_code == library.status_code == 200
    assert "This rule is retired." in detail.text and 'rule-retired' in library.text
    # Retirement advances policy generation even when it leaves no active rules.
    assert public(web, old["before-benign.pdf"]).status_code == 404
    assert public(web, new["new-benign.pdf"]).status_code == 404
    assert web.client.post("/learning/rescan", follow_redirects=False).status_code == 303
    # Retirement is not permission to release previously held/withheld records.
    for name in ("before-positive.pdf", "before-withheld.pdf"):
        assert public(web, old[name]).status_code == 404
    assert public(web, new["new-positive.pdf"]).status_code == 404
    assert public(web, old["before-benign.pdf"]).content == bodies["before-benign.pdf"]


def test_learning_routes_require_staff_and_same_origin_mutations(web):
    rule = propose(web)
    route = f"/learning/rules/{rule['id']}"
    for path in ("/learning", route, route + "/skill.md", route + "/proposal.md",
                 route + "/bundle.zip", route + "/example/0.pdf"):
        assert web.anonymous.get(path).status_code == 401, path
    for path in (f"/learning/from-case/{CASE_ID}", route + "/test",
                 route + "/activate", route + "/retire", "/learning/rescan", "/learning/propose"):
        response = web.anonymous.post(path, data={"digest": rule["digest"]}, follow_redirects=False)
        assert response.status_code == 401, (path, response.text)
        response = web.client.post(path, data={"digest": rule["digest"]},
                                   headers={"origin": "https://foreign.example"}, follow_redirects=False)
        assert response.status_code == 403, path
    assert web.learning.get_rule(rule["id"])["status"] == "draft"
    assert web.client.post("/learning/from-case/unknown-source", follow_redirects=False).status_code == 404


def test_custom_report_fails_clearly_without_a_model_and_creates_no_rule(web):
    response = web.client.post("/learning/propose", data={
        "title": "Fictional custom report", "url": "https://example.invalid/fictional-report",
        "evidence_status": "alleged",
        "summary": "Fictional sanitized summary for a new publication concern. No personal records are included.",
    }, follow_redirects=False)
    assert response.status_code == 400
    assert "require a configured AkashML model" in response.text
    assert web.learning.list_rules() == []


def test_custom_source_claim_is_saved_as_unverified_even_if_submitter_claims_acknowledgment(web):
    from copy import deepcopy
    from gate.learning_proposer import UNVERIFIED
    from gate.learning_sources import CASES
    captured = {}

    def synthetic_proposal(source):
        captured.update(source)
        return deepcopy(CASES[0]["recipe"]), "constructed test candidate; no provider called"

    web.monkeypatch.setattr(web.app, "propose", synthetic_proposal)
    response = web.client.post("/learning/propose", data={
        "title": "Unverified fictional source", "url": "https://example.invalid/unverified-source",
        "evidence_status": "acknowledged",
        "summary": "A submitter alleges an institution acknowledged an exposure. This fictional claim is not verified.",
    }, follow_redirects=False)
    assert response.status_code == 303
    rule = web.learning.list_rules()[0]
    assert rule["status"] == "draft"
    assert captured["evidence_status"] == rule["source"]["evidence_status"] == UNVERIFIED
    assert "Submitter describes evidence as: acknowledged." in rule["source"]["summary"]
    detail = web.client.get(response.headers["location"])
    assert detail.status_code == 200 and UNVERIFIED in detail.text
    skill = web.client.get(f"/learning/rules/{rule['id']}/skill.md")
    assert skill.status_code == 200 and UNVERIFIED in skill.text
