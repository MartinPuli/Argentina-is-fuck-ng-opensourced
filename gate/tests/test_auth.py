"""Request boundaries exercised through the app with fictional PDFs and local state."""

import importlib
from urllib.parse import unquote

import pymupdf
import pytest
from fastapi.testclient import TestClient


PASSWORD = "test-only-staff-password"
AUTH = ("reviewer", PASSWORD)
FORM = {"office": "UGL XXIII Jujuy", "procedure": "Fictional 1/2026", "item": "Chair", "amount": "100"}


@pytest.fixture
def boundary(monkeypatch, tmp_path):
    for name in ("AKASHML_API_KEY", "GUILD_WORKSPACE", "GUILD_AGENT", "CLICKHOUSE_HOST"):
        monkeypatch.setenv(name, "")
    monkeypatch.setenv("GATE_STAFF_PASSWORD", PASSWORD)
    monkeypatch.delenv("GATE_STAFF_USERNAME", raising=False)
    app_module = importlib.import_module("gate.app")
    store = importlib.import_module("gate.store")
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "state.sqlite")
    monkeypatch.setattr(app_module, "events", store.Events())
    with TestClient(app_module.app) as client:
        yield client, app_module, store


def fictional_pdf(pages=1, *, encrypted=False):
    with pymupdf.open() as document:
        for _ in range(pages):
            page = document.new_page()
            page.insert_text((72, 72), "Fictional public purchase: one standard chair.")
        if encrypted:
            return document.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256,
                                    owner_pw="fictional-owner", user_pw="fictional-reader")
        return document.tobytes()


def store_file(app_module, *, decision="hold", filename="fictional.pdf"):
    purchase = app_module.create_purchase("Fictional office", "Test", "Chair", 100)
    content = fictional_pdf()
    ident = app_module.store_attachment(purchase, filename, content, None, decision, [], [], 0)
    return ident, content


def assert_no_purchase(store):
    with store.db() as con:
        assert con.execute("select count(*) from purchases").fetchone()[0] == 0
        assert con.execute("select count(*) from attachments").fetchone()[0] == 0


@pytest.mark.parametrize("path", ["/office", "/purchase/1", "/review", "/internal/file/1", "/dashboard"])
def test_staff_routes_require_credentials(boundary, path):
    client, _, _ = boundary
    response = client.get(path)
    assert response.status_code == 401
    assert response.headers["www-authenticate"].startswith("Basic ")


@pytest.mark.parametrize("path", ["/office", "/purchase/1", "/review", "/internal/file/1", "/dashboard"])
def test_missing_password_disables_staff_routes(boundary, monkeypatch, path):
    client, _, _ = boundary
    monkeypatch.setenv("GATE_STAFF_PASSWORD", "")
    assert client.get(path, auth=AUTH).status_code == 503


def test_missing_password_does_not_close_public_portal(boundary, monkeypatch):
    client, _, _ = boundary
    monkeypatch.setenv("GATE_STAFF_PASSWORD", "")
    assert client.get("/public").status_code == 200
    assert client.get("/public/file/999").status_code == 404
    assert client.post("/demo/seed", headers={"origin": "http://testserver"}).status_code == 503


def test_username_and_password_both_match_configured_identity(boundary, monkeypatch):
    client, _, _ = boundary
    assert client.get("/review", auth=("other-person", PASSWORD)).status_code == 401
    assert client.get("/review", auth=("reviewer", "wrong-password")).status_code == 401
    assert client.get("/review", auth=AUTH).status_code == 200
    monkeypatch.setenv("GATE_STAFF_USERNAME", "institution-reviewer")
    assert client.get("/review", auth=AUTH).status_code == 401
    assert client.get("/review", auth=("institution-reviewer", PASSWORD)).status_code == 200


@pytest.mark.parametrize("headers", [
    {},
    {"origin": "null", "referer": "http://testserver/review"},
    {"origin": "", "referer": "http://testserver/review"},
    {"origin": "https://testserver"},
    {"origin": "http://testserver:81"},
    {"origin": "http://foreign.example"},
    {"origin": "http://testserver/path"},
    {"origin": "http://user@testserver"},
    {"origin": "http://testserver:invalid"},
])
def test_unsafe_or_missing_origin_cannot_mutate(boundary, headers):
    client, app_module, store = boundary
    ident, _ = store_file(app_module)
    response = client.post(f"/review/{ident}", headers=headers, auth=AUTH,
                           data={"action": "approve", "note": "Checked fictional document."})
    assert response.status_code == 403
    with store.db() as con:
        assert con.execute("select decision from attachments where id=?", (ident,)).fetchone()[0] == "hold"


@pytest.mark.parametrize("headers", [
    {"origin": "http://testserver"},
    {"origin": "http://testserver:80"},
    {"referer": "http://testserver/review?filter=held"},
])
def test_same_origin_approval_uses_authenticated_identity(boundary, headers):
    client, app_module, store = boundary
    ident, content = store_file(app_module)
    assert client.get(f"/public/file/{ident}").status_code == 404
    response = client.post(f"/review/{ident}", headers=headers, auth=AUTH,
                           data={"action": "approve", "reviewer": "Forged Administrator",
                                 "note": " Checked fictional document. "}, follow_redirects=False)
    assert response.status_code == 303
    with store.db() as con:
        row = con.execute("select reviewed_by, review_note from attachments where id=?", (ident,)).fetchone()
        assert tuple(row) == ("reviewer", "Checked fictional document.")
        assert con.execute("select actor from events where event='approved'").fetchone()[0] == "reviewer"
    assert client.get(f"/public/file/{ident}").content == content
    repeated = client.post(f"/review/{ident}", headers=headers, auth=AUTH,
                           data={"action": "reject", "note": "A second decision."})
    assert repeated.status_code == 409


@pytest.mark.parametrize("note", ["", "   ", "x" * 2001])
@pytest.mark.parametrize("action", ["approve", "reject"])
def test_review_requires_bounded_explanation(boundary, note, action):
    client, app_module, _ = boundary
    ident, _ = store_file(app_module)
    response = client.post(f"/review/{ident}", headers={"origin": "http://testserver"}, auth=AUTH,
                           data={"action": action, "note": note})
    assert response.status_code == 400
    assert client.get(f"/public/file/{ident}").status_code == 404


def test_withheld_document_cannot_be_approved(boundary):
    client, app_module, _ = boundary
    ident, _ = store_file(app_module, decision="withheld")
    response = client.post(f"/review/{ident}", headers={"origin": "http://testserver"}, auth=AUTH,
                           data={"action": "approve", "note": "Attempt to bypass deterministic block."})
    assert response.status_code == 409
    assert client.get(f"/public/file/{ident}").status_code == 404


@pytest.mark.parametrize("bad", [b"", b"this is not a PDF", b"%PDF-1.7\ninvalid document"])
def test_invalid_pdf_batch_leaves_no_partial_purchase(boundary, bad):
    client, _, store = boundary
    response = client.post("/office", headers={"origin": "http://testserver"}, auth=AUTH, data=FORM,
                           files=[("files", ("valid.pdf", fictional_pdf(), "application/pdf")),
                                  ("files", ("bad.pdf", bad, "application/pdf"))])
    assert response.status_code == 400
    assert_no_purchase(store)


def test_missing_files_does_not_create_purchase(boundary):
    client, _, store = boundary
    response = client.post("/office", headers={"origin": "http://testserver"}, auth=AUTH, data=FORM)
    assert response.status_code == 422
    assert_no_purchase(store)


def test_encrypted_pdf_is_rejected_before_purchase(boundary):
    client, _, store = boundary
    response = client.post("/office", headers={"origin": "http://testserver"}, auth=AUTH, data=FORM,
                           files={"files": ("locked.pdf", fictional_pdf(encrypted=True), "application/pdf")})
    assert response.status_code == 400
    assert_no_purchase(store)


@pytest.mark.parametrize("limit", ["file_count", "per_file", "aggregate", "page_count"])
def test_upload_limits_precede_database_writes(boundary, monkeypatch, limit):
    client, app_module, store = boundary
    content = fictional_pdf(pages=2 if limit == "page_count" else 1)
    count = 1
    if limit == "file_count":
        monkeypatch.setattr(app_module, "MAX_FILES", 1)
        count = 2
    elif limit == "per_file":
        monkeypatch.setattr(app_module, "MAX_FILE_BYTES", len(content) - 1)
    elif limit == "aggregate":
        monkeypatch.setattr(app_module, "MAX_UPLOAD_BYTES", len(content) * 2 - 1)
        count = 2
    else:
        monkeypatch.setattr(app_module, "MAX_PDF_PAGES", 1)
    response = client.post("/office", headers={"origin": "http://testserver"}, auth=AUTH, data=FORM,
                           files=[("files", (f"{n}.pdf", content, "application/pdf")) for n in range(count)])
    assert response.status_code == (413 if limit in {"per_file", "aggregate"} else 400)
    assert_no_purchase(store)


def test_valid_upload_still_reaches_public_enforcement(boundary, monkeypatch):
    client, app_module, store = boundary
    content = fictional_pdf()
    monkeypatch.setattr(app_module, "evaluate", lambda data: (None, "public", ["Synthetic test verdict"], [], 0))
    response = client.post("/office", headers={"origin": "http://testserver"}, auth=AUTH, data=FORM,
                           files={"files": ("technical sheet.pdf", content, "application/pdf")},
                           follow_redirects=False)
    assert response.status_code == 303
    with store.db() as con:
        ident = con.execute("select id from attachments").fetchone()[0]
    assert client.get(f"/public/file/{ident}").content == content


@pytest.mark.parametrize("route", ["public", "internal"])
def test_pdf_responses_have_safe_utf8_filename_and_no_store(boundary, route):
    client, app_module, _ = boundary
    ident, content = store_file(app_module, decision="public", filename='../private/estudio muñón "x"\r\n.pdf')
    response = client.get(f"/{route}/file/{ident}", auth=AUTH if route == "internal" else None)
    assert response.status_code == 200
    assert response.content == content
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    header = response.headers["content-disposition"]
    assert "\r" not in header and "\n" not in header
    assert "../" not in header and "private" not in header
    assert unquote(header.split("filename*=UTF-8''", 1)[1]) == 'estudio muñón "x".pdf'


def test_public_denial_is_not_cacheable(boundary):
    client, app_module, _ = boundary
    ident, _ = store_file(app_module)
    response = client.get(f"/public/file/{ident}")
    assert response.status_code == 404
    assert response.headers["cache-control"] == "no-store"
