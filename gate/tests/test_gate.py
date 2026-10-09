"""Publication promises against fictional fixtures, without sponsor calls or OCR.

Run: uv run python -m pytest -q (from gate/).
OCR is deliberately unavailable here, so image-only fixtures must be held.
Successful synthetic OCR/vision coverage is tested separately in test_coverage.py.
"""

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import dotenv
import pytest
from fastapi.testclient import TestClient

from gate import detect, llm
from gate.detect import cuit_valid, mask, scan
from gate.policy import decide

PDFS = Path(__file__).parents[1] / "fixtures" / "pdfs"
STAFF = ("test-reviewer", "fictional-test-password")
EXPECTED_OFFLINE = {
    "especificacion_tecnica_silla.pdf": "hold",
    "nota_pedido.pdf": "withheld",  # DNI and CUIL; a cleaned copy needs the verifier to go public
    "cotizacion_proveedor.pdf": "hold",
    "justificacion_medica.pdf": "withheld",
    "dni_escaneado.pdf": "hold",  # unread image; do not invent successful OCR
    "certificado_discapacidad.pdf": "hold",  # unread image
    "especificacion_protesis.pdf": "hold",
    "radiografia_muñon.pdf": "hold",
    "especificacion_cama.pdf": "hold",  # context risk cannot be cleared without analysis
}
SAFE_TEXT = {
    "safe_for_public": True, "personal_data": False, "health_data": False,
    "reidentification_risk": "none", "reasons": [],
}


@pytest.fixture(autouse=True)
def offline_environment(monkeypatch, tmp_path):
    """Per-test configuration is restored; no tracked/local database is touched."""
    for var in ("AKASHML_API_KEY", "GUILD_WORKSPACE", "GUILD_AGENT", "CLICKHOUSE_HOST"):
        monkeypatch.setenv(var, "")
    monkeypatch.setenv("GATE_DB", str(tmp_path / "gate.sqlite3"))
    monkeypatch.setenv("GATE_STAFF_USERNAME", STAFF[0])
    monkeypatch.setenv("GATE_STAFF_PASSWORD", STAFF[1])
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: False)

    def unavailable_ocr(*args, **kwargs):
        raise RuntimeError("OCR intentionally unavailable in portable offline tests")

    def unexpected_provider(*args, **kwargs):
        pytest.fail("offline tests must not construct a model provider")

    monkeypatch.setattr(detect.pytesseract, "image_to_string", unavailable_ocr)
    monkeypatch.setattr(llm, "OpenAI", unexpected_provider)


@pytest.fixture
def web(monkeypatch, tmp_path, offline_environment):
    store = importlib.import_module("gate.store")
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "gate.sqlite3")
    app_module = importlib.import_module("gate.app")
    monkeypatch.setattr(app_module, "events", store.Events())
    with TestClient(app_module.app, headers={"origin": "http://testserver"}) as client:
        client.auth = STAFF
        with TestClient(app_module.app) as anonymous:
            yield SimpleNamespace(client=client, anonymous=anonymous, app=app_module, store=store)


def seed(web):
    response = web.client.post("/demo/seed", follow_redirects=False)
    assert response.status_code == 303
    with web.store.db() as con:
        rows = con.execute("select id, purchase_id, filename, decision from attachments order by id").fetchall()
    assert {row["filename"]: row["decision"] for row in rows} == EXPECTED_OFFLINE
    return rows, response.headers["location"]


@pytest.mark.parametrize("name,expected", EXPECTED_OFFLINE.items())
def test_each_fixture_gets_the_expected_offline_decision(name, expected):
    result = scan((PDFS / name).read_bytes())
    decision, _, _ = decide(result, None)
    assert decision == expected
    if name in {"dni_escaneado.pdf", "certificado_discapacidad.pdf", "radiografia_muñon.pdf"}:
        assert any("ocr_failed" in page.coverage_issues for page in result.pages)


@pytest.mark.parametrize("name", ["especificacion_tecnica_silla.pdf", "cotizacion_proveedor.pdf"])
def test_clean_text_fixture_can_publish_with_complete_synthetic_model_result(name):
    """Constructed model output exercises policy, not a live classifier's accuracy."""
    result = scan((PDFS / name).read_bytes())
    assert not result.ocr_used
    assert decide(result, SAFE_TEXT)[0] == "public"
    assert decide(result, None)[0] == "hold"


def test_model_can_add_caution_but_never_release_a_block():
    sensitive = scan((PDFS / "justificacion_medica.pdf").read_bytes())
    assert decide(sensitive, SAFE_TEXT)[0] == "withheld"
    assert decide(sensitive, None)[0] == "withheld"
    clean = scan((PDFS / "especificacion_tecnica_silla.pdf").read_bytes())
    worried = dict(SAFE_TEXT, safe_for_public=False, health_data=True,
                   reidentification_risk="medium", reasons=["mentions a condition"])
    assert decide(clean, worried)[0] == "hold"


def test_findings_never_carry_raw_identifiers():
    checked = 0
    for name in EXPECTED_OFFLINE:
        for finding in scan((PDFS / name).read_bytes()).findings:
            if finding.kind in ("dni", "person_cuil", "affiliate_number"):
                checked += 1
                assert "*" in finding.evidence, (name, finding.evidence)
    assert checked >= 3  # do not pass merely because no identifiers were extracted
    assert mask("31.846.275") == "31.***.275"


def test_company_cuit_is_public_person_cuil_is_not():
    assert cuit_valid("30715839209")
    supplier = scan((PDFS / "cotizacion_proveedor.pdf").read_bytes())
    assert {finding.kind for finding in supplier.findings} == {"company_cuit"}
    assert decide(supplier, SAFE_TEXT)[0] == "public"
    personal = scan((PDFS / "justificacion_medica.pdf").read_bytes())
    assert any(f.kind == "person_cuil" and f.severity == "block" for f in personal.findings)
    assert decide(personal, SAFE_TEXT)[0] == "withheld"


def test_public_portal_never_serves_withheld_or_held_files(web):
    rows, _ = seed(web)
    portal = web.anonymous.get("/public")
    assert portal.status_code == 200
    for row in rows:
        response = web.anonymous.get(f"/public/file/{row['id']}")
        assert response.status_code == 404, row["filename"]
        assert row["filename"] not in portal.text
        assert web.anonymous.get(f"/internal/file/{row['id']}").status_code == 401
        internal = web.client.get(f"/internal/file/{row['id']}")
        assert internal.status_code == 200
        assert internal.content == (PDFS / row["filename"]).read_bytes()

    clean = next(row for row in rows if row["filename"] == "especificacion_tecnica_silla.pdf")
    note = "Inspected the fictional specification; it contains equipment requirements only."
    approved = web.client.post(f"/review/{clean['id']}", data={
        "action": "approve", "reviewer": "forged-display-name", "note": note,
    }, follow_redirects=False)
    assert approved.status_code == 303
    public = web.anonymous.get(f"/public/file/{clean['id']}")
    assert public.status_code == 200
    assert public.content == (PDFS / clean["filename"]).read_bytes()
    assert public.headers["cache-control"] == "no-store"
    with web.store.db() as con:
        saved = con.execute("select reviewed_by, review_note from attachments where id=?", (clean["id"],)).fetchone()
    assert saved["reviewed_by"] == STAFF[0]
    assert saved["review_note"] == note
    portal = web.anonymous.get("/public").text
    for row in rows:
        assert row["filename"] not in portal
        assert (f'href="/public/file/{row["id"]}"' in portal) == (row["id"] == clean["id"])
    assert web.app.public_filename(clean["purchase_id"], clean["id"]) in portal

    blocked = next(row for row in rows if row["decision"] == "withheld")
    rejected = web.client.post(f"/review/{blocked['id']}", data={
        "action": "approve", "note": "Attempt to override a deterministic block.",
    }, follow_redirects=False)
    assert rejected.status_code == 409
    assert web.anonymous.get(f"/public/file/{blocked['id']}").status_code == 404


def test_review_requires_a_reason_and_can_keep_a_held_file_internal(web):
    rows, _ = seed(web)
    held = next(row for row in rows if row["filename"] == "especificacion_cama.pdf")
    url = f"/review/{held['id']}"
    assert web.client.post(url, data={"action": "approve"}).status_code == 400
    assert web.client.post(url, data={"action": "approve", "note": "   "}).status_code == 400
    with web.store.db() as con:
        assert con.execute("select decision from attachments where id=?", (held["id"],)).fetchone()[0] == "hold"
    response = web.client.post(url, data={
        "action": "reject", "note": "Fictional details could identify an individual; keep internal.",
    }, follow_redirects=False)
    assert response.status_code == 303
    with web.store.db() as con:
        row = con.execute("select decision, reviewed_by from attachments where id=?", (held["id"],)).fetchone()
    assert row["decision"] == "withheld" and row["reviewed_by"] == STAFF[0]
    assert web.anonymous.get(f"/public/file/{held['id']}").status_code == 404


def test_cross_site_approval_is_rejected(web):
    """A foreign page must not be able to approve a held file."""
    data = {"action": "approve", "note": "Synthetic review reason."}
    evil = web.client.post("/review/1", data=data,
                           headers={"origin": "https://evil.example"}, follow_redirects=False)
    assert evil.status_code == 403
    no_origin = web.anonymous.post("/review/1", data=data, auth=STAFF, follow_redirects=False)
    assert no_origin.status_code == 403


def test_public_page_says_the_data_is_fictional(web):
    portal = web.anonymous.get("/public")
    assert portal.status_code == 200
    assert "Demo · fictional data" in portal.text
    assert "Demo. All people and records are fictional." in portal.text


@pytest.mark.parametrize("route,label", [
    ("/", "Documents"),
    ("/office", "Upload"),
    ("/review", "No files waiting for review."),
    ("/public", "No purchases published yet."),
    ("/dashboard", "No findings recorded yet."),
])
def test_screen_empty_states_render(web, route, label):
    response = web.client.get(route)
    assert response.status_code == 200
    assert label in response.text
    assert 'lang="en"' in response.text
    assert 'id="content"' in response.text


def test_purchase_without_attachments_has_a_useful_empty_state(web):
    purchase = web.app.create_purchase("Synthetic office", "DEMO-EMPTY", "Empty test purchase", 0)
    response = web.client.get(f"/purchase/{purchase['id']}")
    assert response.status_code == 200
    assert "No attachments in this purchase" in response.text
    assert web.client.get("/purchase/999999").status_code == 404


def test_all_populated_screens_render_current_decisions(web):
    rows, purchase_url = seed(web)
    clean = next(row for row in rows if row["filename"] == "especificacion_tecnica_silla.pdf")
    assert web.client.post(f"/review/{clean['id']}", data={
        "action": "approve", "note": "Verified fictional equipment requirements only.",
    }, follow_redirects=False).status_code == 303
    expected_labels = {
        "/": ["Documents"],
        "/office": ["Supporting attachments", "Load synthetic files"],
        purchase_url: ["Attachment decisions", "Reviewer approved", "Kept internal", "Needs review"],
        "/review": ["Decision reason", "Keep private", "Publish original", STAFF[0]],
        "/public": ["Published purchases", web.app.public_filename(clean["purchase_id"], clean["id"])],
        "/dashboard": ["Decisions by office", "Human review history", STAFF[0]],
    }
    for route, labels in expected_labels.items():
        response = web.client.get(route)
        assert response.status_code == 200, route
        for label in labels:
            assert label in response.text, (route, label)


def add_attachment(web, decision, public_pdf=None, manifest=None, verifier=None):
    """Insert one fictional row directly, as if the sanitizer had already run."""
    purchase = web.app.create_purchase("Synthetic office", "DEMO-CLEAN", "Cleaned copy test", 0)
    original = (PDFS / "nota_pedido.pdf").read_bytes()
    with web.store.db() as con:
        att_id = con.execute(
            "insert into attachments (purchase_id, filename, sha256, pdf, decision, reasons, findings,"
            " model, created_at, public_pdf, manifest, verifier) values (?,?,?,?,?,?,?,?,?,?,?,?)",
            (purchase["id"], "nota_pedido.pdf", "0" * 64, original, decision, "[]", "[]", "null", 0.0,
             public_pdf, json.dumps(manifest) if manifest is not None else None,
             json.dumps(verifier) if verifier is not None else None)).lastrowid
    web.app.learning.record_check(att_id, web.app.learning.revision())
    return att_id, original


CLEANED = b"%PDF-1.4 fictional cleaned copy"
MANIFEST = [{"page": 1, "category": "DNI", "masked": "31.***.275"}]


def test_internal_clean_preview_is_staff_only_and_404_without_a_copy(web):
    plain, _ = add_attachment(web, "hold")
    assert web.client.get(f"/internal/clean/{plain}").status_code == 404
    assert web.client.get("/internal/clean/999999").status_code == 404
    cleaned, _ = add_attachment(web, "hold", CLEANED, MANIFEST)
    assert web.anonymous.get(f"/internal/clean/{cleaned}").status_code == 401
    response = web.client.get(f"/internal/clean/{cleaned}")
    assert response.status_code == 200
    assert response.content == CLEANED
    assert response.headers["cache-control"] == "no-store"
    assert web.anonymous.get(f"/public/file/{cleaned}").status_code == 404  # held stays private


def test_public_file_serves_only_the_cleaned_copy(web):
    att_id, original = add_attachment(web, "cleaned", CLEANED, MANIFEST,
                                      {"verdict": "PASS", "text": "ok", "url": "javascript:alert(1)"})
    response = web.anonymous.get(f"/public/file/{att_id}")
    assert response.status_code == 200
    assert response.content == CLEANED and response.content != original
    assert "Cleaned copy" in web.anonymous.get("/public").text
    with web.store.db() as con:
        pid = con.execute("select purchase_id from attachments where id=?", (att_id,)).fetchone()[0]
    page = web.client.get(f"/purchase/{pid}").text
    for label in ("Removed", "31.***.275", "Verifier PASS", f"/public/file/{att_id}", "Original (internal)"):
        assert label in page, label
    assert "javascript:" not in page  # verifier links must be web URLs


def test_activity_and_review_say_approval_publishes_the_cleaned_copy(web):
    plain, _ = add_attachment(web, "hold")
    cleaned, _ = add_attachment(web, "hold", CLEANED, MANIFEST + [
        {"page": 2, "category": "CUIL", "masked": "20-3*******-5"}])
    waiting = {item["id"]: item for item in web.client.get("/api/activity").json()["waiting"]}
    assert waiting[plain]["has_clean"] is False and waiting[plain]["removed"] == []
    assert waiting[cleaned]["has_clean"] is True and waiting[cleaned]["removed"] == ["CUIL", "DNI"]
    review = web.client.get("/review").text
    assert review.count("Publish cleaned copy") == 1 and review.count("Publish original") == 1
    assert f"/internal/clean/{cleaned}" in review
    approved = web.client.post(f"/review/{cleaned}", data={
        "action": "approve", "note": "Inspected the cleaned fictional copy."}, follow_redirects=False)
    assert approved.status_code == 303
    assert web.anonymous.get(f"/public/file/{cleaned}").content == CLEANED


def fictional_pdf(text):
    import pymupdf
    with pymupdf.open() as document:
        document.new_page().insert_text((72, 72), text, fontsize=11)
        return document.tobytes()


def cleaned_row(web, original, public_copy):
    """A published cleaned copy, current against the active rules (Semgrep review fixes)."""
    from gate import learning
    purchase = web.app.create_purchase("UGL XXX Chivilcoy", "Ficticio 1/2026", "Silla de ruedas", 1000.0)
    with web.store.db() as con:
        att_id = con.execute(
            "insert into attachments (purchase_id, filename, sha256, pdf, public_pdf, decision, reasons,"
            " findings, model, created_at) values (?,?,?,?,?,?,?,?,?,?)",
            (purchase["id"], "nota.pdf", "x", original, public_copy, "cleaned", "[]", "[]", "null", 0),
        ).lastrowid
    learning.record_check(att_id, learning.revision())
    return att_id


ORIGINAL = "Documento ficticio. DNI: 31.846.275. Registro sintetico para una prueba."


def test_recheck_restricts_a_cleaned_copy_that_still_identifies_someone(web):
    leaky_copy = fictional_pdf(ORIGINAL)  # the cleaned copy itself still carries the DNI
    att_id = cleaned_row(web, fictional_pdf(ORIGINAL), leaky_copy)
    assert web.anonymous.get(f"/public/file/{att_id}").content == leaky_copy
    assert web.client.post("/learning/rescan", follow_redirects=False).status_code == 303
    assert web.anonymous.get(f"/public/file/{att_id}").status_code == 404
    with web.store.db() as con:
        assert con.execute("select decision from attachments where id=?", (att_id,)).fetchone()[0] == "withheld"


def test_recheck_keeps_a_clean_cleaned_copy_public(web):
    clean_copy = fictional_pdf("Documento ficticio. Silla de ruedas estandar, 1 unidad.")
    att_id = cleaned_row(web, fictional_pdf(ORIGINAL), clean_copy)
    assert web.client.post("/learning/rescan", follow_redirects=False).status_code == 303
    response = web.anonymous.get(f"/public/file/{att_id}")
    assert response.status_code == 200 and response.content == clean_copy


def test_cleaned_decision_never_falls_back_to_the_original(web):
    att_id = cleaned_row(web, fictional_pdf(ORIGINAL), None)
    assert web.anonymous.get(f"/public/file/{att_id}").status_code == 404
