"""Operational History uses recorded audit events, never generated benchmark rows."""

import importlib

import pytest
from fastapi.testclient import TestClient

PASSWORD = "test-only-history-password"
AUTH = ("reviewer", PASSWORD)

@pytest.fixture
def web(monkeypatch, tmp_path):
    for name in ("AKASHML_API_KEY", "GUILD_WORKSPACE", "GUILD_AGENT", "CLICKHOUSE_HOST"):
        monkeypatch.setenv(name, "")
    monkeypatch.setenv("GATE_STAFF_PASSWORD", PASSWORD)
    monkeypatch.delenv("GATE_STAFF_USERNAME", raising=False)
    app_module = importlib.import_module("gate.app")
    store = importlib.import_module("gate.store")
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "state.sqlite")
    events = store.Events()
    monkeypatch.setattr(app_module, "events", events)
    with TestClient(app_module.app) as client:
        yield client, events, monkeypatch


def test_dashboard_uses_local_audit_without_clickhouse(web):
    client, events, _ = web
    assert events.history() is None
    response = client.get("/dashboard", auth=AUTH)
    assert response.status_code == 200
    assert "Decisions by office" in response.text
    assert "No findings recorded yet." in response.text
    assert "audit events · local SQLite" in response.text
    assert "Simulated telemetry" not in response.text
    assert "History needs ClickHouse" not in response.text


def test_operational_history_and_workspace_count_actual_events(web):
    client, events, monkeypatch = web
    monkeypatch.setattr(events, "history", lambda: pytest.fail("Operational pages must not query benchmark rows"))
    for index, decision in enumerate(("public", "hold", "withheld"), 1):
        events.log("decision", "Test office", 1, index, "fictional.pdf", decision,
                   ["dni"] if decision != "public" else [], latency_ms=index * 1000)
    events.log("approved", "Test office", 1, 2, "fictional.pdf", "approved", actor="test-reviewer")
    response = client.get("/dashboard", auth=AUTH)
    assert response.status_code == 200
    text = response.text
    assert "<title>History</title>" in text
    assert "<strong>4</strong><span>audit events" in text
    assert "<strong>3</strong><span>document decisions" in text
    assert "<strong>2.0<small>s</small></strong>" in text
    assert "Test office" in text and "test-reviewer" in text
    assert "Dni<b>2</b>" in text
    assert "Simulated" not in text and "1,000,000" not in text
    home = client.get("/", auth=AUTH)
    assert home.status_code == 200 and "4 audit events" in home.text
    assert "1,000,000" not in home.text
