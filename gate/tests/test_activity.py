"""Real background workers with synthetic PDFs; providers remain local fakes."""

import importlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import dotenv
import pymupdf
import pytest
from fastapi.testclient import TestClient

from gate import activity, learning, llm, store

AUTH = ("live-reviewer", "fictional-live-password")
FORM = {"office": "Fictional office", "procedure": "LIVE-1", "item": "Office equipment", "amount": "10"}
SAFE = {"safe_for_public": True, "personal_data": False, "health_data": False,
        "reidentification_risk": "none", "reasons": []}


def pdf(text="Fictional public specification: one standard office chair."):
    with pymupdf.open() as doc:
        doc.new_page().insert_text((72, 72), text)
        return doc.tobytes()


@pytest.fixture
def live(monkeypatch, tmp_path):
    for key in ("AKASHML_API_KEY", "GUILD_WORKSPACE", "GUILD_AGENT", "CLICKHOUSE_HOST"):
        monkeypatch.setenv(key, "")
    monkeypatch.setenv("GATE_STAFF_USERNAME", AUTH[0])
    monkeypatch.setenv("GATE_STAFF_PASSWORD", AUTH[1])
    monkeypatch.setenv("GATE_OPEN_DEMO", "0")
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **kw: False)
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "live.sqlite")
    module = importlib.import_module("gate.app")
    monkeypatch.setattr(module, "events", store.Events())
    monkeypatch.setattr(llm, "review", lambda _text: dict(SAFE))
    monkeypatch.setattr(module.agent, "configured", lambda: False)
    # These tests isolate queue/policy outcomes; copy generation has its own tests.
    monkeypatch.setattr(module.sanitize, "build", lambda *args, **kwargs: None)
    pool = ThreadPoolExecutor(max_workers=2)
    monkeypatch.setattr(module, "LIVE_EXECUTOR", pool)
    monkeypatch.setattr(module, "LIVE_CAPACITY", threading.BoundedSemaphore(32))
    with activity._lock:
        activity._jobs.clear()
    blockers = []
    with TestClient(module.app, headers={"origin": "http://testserver"}) as client:
        client.auth = AUTH
        try:
            yield SimpleNamespace(client=client, app=module, monkeypatch=monkeypatch, blockers=blockers)
        finally:
            for event in blockers:
                event.set()
            pool.shutdown(wait=True)


def upload(live, content=None):
    return live.client.post("/live/upload", data=FORM,
                            files={"files": ("fictional.pdf", content or pdf(), "application/pdf")},
                            follow_redirects=False)


def finished(live):
    deadline = time.monotonic() + 4
    while time.monotonic() < deadline:
        result = live.client.get("/api/activity").json()
        if result["jobs"] and all(job["done"] for job in result["jobs"]):
            return result
        time.sleep(0.01)
    pytest.fail("background fixture did not complete")


def enable_rule():
    spec = {"title": "Fictional document marker", "groups": [["sensitive synthetic marker"]],
            "action": "withheld", "rationale": "Test marker only", "improvements": [],
            "tests": [{"name": "positive", "text": "sensitive synthetic marker", "should_match": True},
                      {"name": "control", "text": "ordinary public specification", "should_match": False}]}
    source = {"title": "Fictional source", "url": "https://example.org/test",
              "evidence_status": "fictional", "summary": "Local synthetic test only."}
    rule_id = learning.create_candidate(spec, source, AUTH[0])
    result = learning.run_tests(rule_id)
    return learning.activate(rule_id, result["digest"], AUTH[0])


@pytest.mark.parametrize("route", ["/live", "/api/activity", "/exposures"])
def test_live_endpoints_require_configured_staff(live, route):
    assert live.client.get(route, auth=("wrong", AUTH[1])).status_code == 401
    live.monkeypatch.setenv("GATE_STAFF_PASSWORD", "")
    assert live.client.get(route).status_code == 503


@pytest.mark.parametrize("route", ["/live/upload", "/live/demo/seed"])
def test_live_mutations_require_same_origin(live, route):
    response = live.client.post(route, headers={"origin": "null"})
    assert response.status_code == 403
    with store.db() as con:
        assert con.execute("select count(*) from purchases").fetchone()[0] == 0


def test_live_upload_returns_before_work_finishes_and_attributes_submitter(live):
    entered, release = threading.Event(), threading.Event()
    live.blockers.append(release)
    original = live.app.evaluate
    def slow(data, job=None):
        entered.set()
        assert release.wait(3)
        return original(data, job)
    live.monkeypatch.setattr(live.app, "evaluate", slow)
    response = upload(live)
    assert response.status_code == 303 and response.headers["location"] == "/live"
    assert entered.wait(1)
    result = live.client.get("/api/activity")
    assert result.headers["cache-control"] == "no-store"
    assert result.json()["counts"]["processing"] == 1
    assert result.json()["counts"]["published"] == 0
    assert result.json()["jobs"][0]["attachment_id"] is None
    with store.db() as con:
        assert con.execute("select count(*) from attachments").fetchone()[0] == 0
        assert con.execute("select actor from events where event='submitted'").fetchone()[0] == AUTH[0]
    release.set()
    result = finished(live)
    assert result["counts"]["published"] == 1 and result["counts"]["processing"] == 0
    ident = result["jobs"][0]["attachment_id"]
    assert live.client.get(f"/public/file/{ident}", auth=None).status_code == 200


def test_background_worker_failure_is_private_without_exception_text(live):
    def broken(*args, **kwargs):
        raise RuntimeError("SENSITIVE-SYNTHETIC-ERROR-TEXT")
    live.monkeypatch.setattr(live.app, "evaluate", broken)
    assert upload(live).status_code == 303
    result = finished(live)
    assert "SENSITIVE-SYNTHETIC" not in str(result)
    assert result["counts"]["published"] == 0 and result["counts"]["blocked"] == 1
    ident = result["jobs"][0]["attachment_id"]
    assert live.client.get(f"/public/file/{ident}").status_code == 404
    assert live.client.post(f"/review/{ident}", data={"action": "approve", "note": "Try bypass"}).status_code == 409


def test_missing_analysis_is_held_and_note_uses_authenticated_identity(live):
    live.monkeypatch.setattr(llm, "review", lambda _text: None)
    assert upload(live).status_code == 303
    result = finished(live)
    assert result["counts"]["waiting"] == 1 and result["counts"]["published"] == 0
    row = result["waiting"][0]
    assert row["current"] and row["can_approve"]
    route = f"/review/{row['id']}"
    assert live.client.post(route, data={"action": "approve", "note": ""}).status_code == 400
    approved = live.client.post(route, data={"action": "approve", "note": "Inspected fictional PDF.",
                                             "reviewer": "forged"}, follow_redirects=False)
    assert approved.status_code == 303
    with store.db() as con:
        assert con.execute("select reviewed_by from attachments where id=?", (row["id"],)).fetchone()[0] == AUTH[0]
    result = live.client.get("/api/activity").json()
    assert result["counts"]["published"] == 1 and result["waiting"] == []


def test_live_rules_enforce_new_files_and_update_stale_activity(live):
    body = pdf("Fictional data. Sensitive synthetic marker for this publication check.")
    assert upload(live, body).status_code == 303
    before = finished(live)
    old_id = before["jobs"][0]["attachment_id"]
    assert before["counts"]["published"] == 1
    enable_rule()
    changed = live.client.get("/api/activity").json()
    assert changed["counts"]["published"] == 0 and changed["counts"]["stale"] == 1
    assert changed["jobs"][0]["decision"] == "stale"
    assert live.client.get(f"/public/file/{old_id}").status_code == 404
    assert upload(live, body).status_code == 303
    after = finished(live)
    assert after["counts"]["blocked"] == 1
    assert after["jobs"][0]["decision"] == "withheld"


def test_verified_cleaned_copy_is_counted_and_still_requires_current_rules(live):
    original = pdf("Fictional original. DNI: 31.846.275. Synthetic identity fixture.")
    cleaned = pdf("Fictional public specification with no identity reference.")
    # This verifies integration/byte selection, not sanitizer or provider accuracy.
    candidate = SimpleNamespace(pdf=cleaned, text="Fictional public specification.", verified=True,
                                manifest=[{"category": "synthetic test identifier"}])
    live.monkeypatch.setattr(live.app.sanitize, "build", lambda *args, **kwargs: candidate)
    live.monkeypatch.setattr(live.app.agent, "configured", lambda: True)
    live.monkeypatch.setattr(live.app.agent, "verify", lambda *args, **kwargs:
                            {"verdict": "PASS", "text": "Fictional test verdict", "url": "", "latency_ms": 0})
    assert upload(live, original).status_code == 303
    result = finished(live)
    ident = result["jobs"][0]["attachment_id"]
    assert result["jobs"][0]["decision"] == "cleaned"
    assert result["counts"]["published"] == 1 and result["counts"]["blocked"] == 0
    assert live.client.get(f"/public/file/{ident}").content == cleaned
    assert live.client.get(f"/internal/file/{ident}").content == original
    enable_rule()
    result = live.client.get("/api/activity").json()
    assert result["counts"]["published"] == 0 and result["counts"]["stale"] == 1
    assert result["jobs"][0]["decision"] == "stale"
    assert live.client.get(f"/public/file/{ident}").status_code == 404


def test_rule_change_during_worker_keeps_completed_file_stale(live):
    scanned, release = threading.Event(), threading.Event()
    live.blockers.append(release)
    original = live.app.evaluate
    def race(data, job=None):
        result = original(data, job)
        scanned.set()
        assert release.wait(3)
        return result
    live.monkeypatch.setattr(live.app, "evaluate", race)
    assert upload(live).status_code == 303 and scanned.wait(1)
    enable_rule()
    release.set()
    result = finished(live)
    assert result["counts"]["published"] == 0 and result["jobs"][0]["stale"]
    assert live.client.get(f"/public/file/{result['jobs'][0]['attachment_id']}").status_code == 404


def test_queue_full_leaves_no_purchase(live):
    live.monkeypatch.setattr(live.app, "LIVE_CAPACITY", threading.BoundedSemaphore(0))
    assert upload(live).status_code == 503
    with store.db() as con:
        assert con.execute("select count(*) from purchases").fetchone()[0] == 0
    assert activity.snapshot() == []


@pytest.mark.parametrize("bad", [b"not a pdf", b"%PDF-1.7\ninvalid"])
def test_live_invalid_pdf_creates_no_purchase(live, bad):
    assert upload(live, bad).status_code == 400
    with store.db() as con:
        assert con.execute("select count(*) from purchases").fetchone()[0] == 0


def test_live_file_limit_precedes_queue(live):
    live.monkeypatch.setattr(live.app, "MAX_FILE_BYTES", 1)
    assert upload(live).status_code == 413
    assert activity.snapshot() == []


def test_live_demo_uses_validated_background_batches(live):
    live.monkeypatch.setattr(live.app, "evaluate", lambda data, job=None:
                            (None, "hold", ["Synthetic offline fixture"], [], 0, learning.revision()))
    specs = json.loads((live.app.FIXTURES / "purchases.json").read_text())
    expected = sum(len(spec["files"]) for spec in specs)
    response = live.client.post("/live/demo/seed", follow_redirects=False)
    assert response.status_code == 303 and response.headers["location"] == "/live"
    result = finished(live)
    assert len(result["jobs"]) == expected and result["counts"]["waiting"] == expected
    assert result["counts"]["published"] == 0
    with store.db() as con:
        assert con.execute("select count(*) from purchases").fetchone()[0] == len(specs)
        assert {row[0] for row in con.execute("select actor from events where event='submitted'")} == {AUTH[0]}


def test_executor_rejection_is_terminal_and_releases_queue_slot(live):
    class ClosedExecutor:
        def submit(self, *args, **kwargs):
            raise RuntimeError("closed")
    live.monkeypatch.setattr(live.app, "LIVE_EXECUTOR", ClosedExecutor())
    live.monkeypatch.setattr(live.app, "LIVE_CAPACITY", threading.BoundedSemaphore(1))
    assert upload(live).status_code == 303
    result = finished(live)
    assert result["jobs"][0]["decision"] == "error"
    assert result["counts"]["published"] == result["counts"]["processing"] == 0
    assert live.app.LIVE_CAPACITY.acquire(blocking=False)
    live.app.LIVE_CAPACITY.release()
    with store.db() as con:
        assert con.execute("select count(*) from attachments").fetchone()[0] == 0


def test_activity_snapshot_does_not_expose_mutable_internal_state():
    job = activity.start({"id": 1, "office": "Fictional"}, "Chair", "fictional.pdf", ["Read"])
    activity.step(job, "Read", "running")
    snapshot = activity.snapshot()
    snapshot[0]["steps"][0]["status"] = "forged"
    assert activity.snapshot()[0]["steps"][0]["status"] == "running"
