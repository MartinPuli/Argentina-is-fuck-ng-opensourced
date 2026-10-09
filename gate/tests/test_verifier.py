"""Synthetic byte-level checks for asynchronous cleaned-copy publication guards."""

import hashlib
import importlib
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import dotenv
import pymupdf
import pytest
from fastapi.testclient import TestClient

AUTH = ("verification-reviewer", "fictional-verifier-password")
PASS = {"verdict": "PASS", "text": "Synthetic verifier verdict", "url": "", "latency_ms": 0}
SAFE = "Fictional public purchase specification for one standard office chair."
MARKER = "synthetic sensitive marker"


def pdf(text):
    with pymupdf.open() as document:
        document.new_page().insert_text((72, 72), text)
        return document.tobytes()


@pytest.fixture
def verifier(monkeypatch, tmp_path):
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **kw: False)
    for key in ("AKASHML_API_KEY", "GUILD_WORKSPACE", "GUILD_AGENT", "CLICKHOUSE_HOST"):
        monkeypatch.setenv(key, "")
    monkeypatch.setenv("GATE_OPEN_DEMO", "0")
    monkeypatch.setenv("GATE_STAFF_USERNAME", AUTH[0])
    monkeypatch.setenv("GATE_STAFF_PASSWORD", AUTH[1])
    store = importlib.import_module("gate.store")
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "verification.sqlite")
    app = importlib.import_module("gate.app")
    learning = importlib.import_module("gate.learning")
    monkeypatch.setattr(app, "events", store.Events())
    monkeypatch.setattr(app.agent, "configured", lambda: False)
    monkeypatch.setattr(app.sanitize, "build", lambda *a, **kw: None)
    monkeypatch.setattr(app.agent, "verify", lambda *a, **kw: dict(PASS))
    with TestClient(app.app, headers={"origin": "http://testserver"}) as client:
        client.auth = AUTH
        yield SimpleNamespace(app=app, store=store, learning=learning, client=client, monkeypatch=monkeypatch)


def prepare(verifier, *, original=SAFE, candidate_text=SAFE, decision="withheld"):
    purchase = verifier.app.create_purchase("Fictional office", "VERIFY-1", "Chair", 1)
    original_pdf, candidate_pdf = pdf(original), pdf(candidate_text)
    ident = verifier.app.store_attachment(purchase, "fictional.pdf", original_pdf, None,
                                         decision, ["Fictional original restriction"], [], 0)
    candidate = SimpleNamespace(pdf=candidate_pdf, verified=True, text="WRONG-CACHED-TEXT",
                                manifest=[{"category": "synthetic identifier"}])
    with verifier.store.db() as con:
        con.execute("update attachments set public_pdf=? where id=?", (candidate_pdf, ident))
        state = verifier.app.verifier_state(con, ident)
    args = (ident, purchase, "fictional.pdf", candidate, decision, verifier.learning.revision(),
            state, hashlib.sha256(candidate_pdf).hexdigest())
    return SimpleNamespace(id=ident, original=original_pdf, candidate=candidate, args=args)


def record(verifier, ident):
    with verifier.store.db() as con:
        return dict(con.execute("select * from attachments where id=?", (ident,)).fetchone())


def activate(verifier, action="withheld"):
    spec = {"title": "Synthetic candidate rule", "groups": [[MARKER]], "action": action,
            "rationale": "Fictional fixture", "improvements": [],
            "tests": [{"name": "positive", "text": MARKER, "should_match": True},
                      {"name": "control", "text": SAFE, "should_match": False}]}
    source = {"title": "Fictional case", "url": "https://example.org/fictional",
              "evidence_status": "fictional", "summary": "Owned synthetic fixture."}
    ident = verifier.learning.create_candidate(spec, source, AUTH[0])
    result = verifier.learning.run_tests(ident)
    verifier.learning.activate(ident, result["digest"], AUTH[0])


def late_pass(verifier, case, change):
    entered, release = threading.Event(), threading.Event()
    def wait_for_change(*args):
        entered.set()
        assert release.wait(3)
        return dict(PASS)
    verifier.monkeypatch.setattr(verifier.app.agent, "verify", wait_for_change)
    with ThreadPoolExecutor(max_workers=1) as pool:
        worker = pool.submit(verifier.app.verify_in_background, *case.args)
        try:
            assert entered.wait(2)
            change()
        finally:
            release.set()
            worker.result(timeout=3)


def test_pass_uses_candidate_bytes_and_serves_only_that_copy(verifier):
    case = prepare(verifier)
    received = []
    verifier.monkeypatch.setattr(verifier.app.agent, "verify", lambda text, manifest:
                                received.append(text) or dict(PASS))
    verifier.app.verify_in_background(*case.args)
    assert SAFE in received[0] and "WRONG-CACHED-TEXT" not in received[0]
    assert record(verifier, case.id)["decision"] == "cleaned"
    assert verifier.client.get(f"/public/file/{case.id}").content == case.candidate.pdf
    assert verifier.client.get(f"/internal/file/{case.id}").content == case.original


def test_late_pass_cannot_replace_a_new_rule_recheck_block(verifier):
    case = prepare(verifier, original=SAFE + " " + MARKER, decision="hold")
    def change():
        activate(verifier)
        response = verifier.client.post("/learning/rescan", follow_redirects=False)
        assert response.status_code == 303
        assert record(verifier, case.id)["decision"] == "withheld"
        assert verifier.learning.current(case.id)
    late_pass(verifier, case, change)
    assert record(verifier, case.id)["decision"] == "withheld"
    assert record(verifier, case.id)["verifier"] is None
    assert verifier.client.get(f"/public/file/{case.id}").status_code == 404


@pytest.mark.parametrize("action,expected", [("reject", "withheld"), ("approve", "approved")])
def test_late_pass_does_not_replace_staff_decision(verifier, action, expected):
    case = prepare(verifier, decision="hold")
    def change():
        response = verifier.client.post(f"/review/{case.id}", data={"action": action, "note": "Inspected synthetic copy."},
                                        follow_redirects=False)
        assert response.status_code == 303
    late_pass(verifier, case, change)
    row = record(verifier, case.id)
    assert row["decision"] == expected and row["reviewed_by"] == AUTH[0]
    assert row["verifier"] is None


@pytest.mark.parametrize("action", ["withheld", "hold"])
def test_learned_phrase_in_actual_candidate_prevents_automatic_publication(verifier, action):
    activate(verifier, action)
    case = prepare(verifier, candidate_text=SAFE + " " + MARKER)
    calls = []
    verifier.monkeypatch.setattr(verifier.app.agent, "verify", lambda *a: calls.append(a) or dict(PASS))
    verifier.app.verify_in_background(*case.args)
    assert calls == []
    assert record(verifier, case.id)["decision"] == "withheld"
    assert verifier.client.get(f"/public/file/{case.id}").status_code == 404


def test_changed_candidate_cannot_inherit_an_old_pass(verifier):
    case = prepare(verifier, decision="hold")
    def change():
        with verifier.store.db() as con:
            con.execute("update attachments set public_pdf=? where id=?", (pdf(SAFE + " changed"), case.id))
    late_pass(verifier, case, change)
    assert record(verifier, case.id)["decision"] == "hold"
    assert verifier.client.get(f"/public/file/{case.id}").status_code == 404


def test_verifier_failure_preserves_existing_block(verifier):
    case = prepare(verifier)
    verifier.monkeypatch.setattr(verifier.app.agent, "verify", lambda *a:
                                {**PASS, "verdict": "FAIL", "text": "Fictional rejection"})
    verifier.app.verify_in_background(*case.args)
    assert record(verifier, case.id)["decision"] == "withheld"
    assert verifier.client.get(f"/public/file/{case.id}").status_code == 404


def test_incomplete_candidate_extraction_is_not_automatically_published(verifier):
    from gate.detect import Scan
    case = prepare(verifier)
    verifier.monkeypatch.setattr(verifier.app, "scan", lambda _pdf: Scan([], coverage_issues=["synthetic_failure"]))
    calls = []
    verifier.monkeypatch.setattr(verifier.app.agent, "verify", lambda *a: calls.append(a) or dict(PASS))
    verifier.app.verify_in_background(*case.args)
    assert not calls and record(verifier, case.id)["decision"] == "withheld"


def test_recheck_restricts_cleaned_decision_like_other_published_copies(verifier):
    case = prepare(verifier, original=SAFE + " " + MARKER)
    verifier.app.verify_in_background(*case.args)
    assert record(verifier, case.id)["decision"] == "cleaned"
    activate(verifier)
    response = verifier.client.post("/learning/rescan", follow_redirects=False)
    assert response.status_code == 303 and record(verifier, case.id)["decision"] == "withheld"
    assert verifier.learning.current(case.id)
    assert verifier.client.get(f"/public/file/{case.id}").status_code == 404
