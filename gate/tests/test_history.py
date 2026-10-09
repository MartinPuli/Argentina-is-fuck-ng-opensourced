"""The audit page's simulated-history section, with and without ClickHouse."""

import importlib

import pytest
from fastapi.testclient import TestClient

PASSWORD = "test-only-history-password"
AUTH = ("reviewer", PASSWORD)

FAKE_HISTORY = {
    "total": {"value": 1_000_000, "ms": 12.3},
    "by_office": {"rows": [("UGL XIX Misiones", 13364, 52.4), ("UGL I La Plata", 13642, 27.1)], "ms": 31.0},
    "kinds": {"rows": [("dni", 90850), ("model_context", 53839)], "ms": 41.5},
    "monthly": {"rows": [("Sep 2026", 41867, 30.1), ("Oct 2026", 12943, 29.8)], "ms": 36.2},
    "policy": {"files": 29564, "offices": 35, "kind": "model_context", "ms": 49.6},
}


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


def test_dashboard_hides_history_without_clickhouse(web):
    client, events, _ = web
    assert events.history() is None
    response = client.get("/dashboard", auth=AUTH)
    assert response.status_code == 200
    assert "Decisions by office" in response.text
    assert "Simulated telemetry" not in response.text


def test_dashboard_shows_simulated_history_with_query_times(web):
    client, events, monkeypatch = web
    monkeypatch.setattr(events, "history", lambda: FAKE_HISTORY)
    response = client.get("/dashboard", auth=AUTH)
    assert response.status_code == 200
    text = response.text
    assert "PAMI-scale history" in text
    assert "1,000,000" in text
    assert "Simulated telemetry, not real PAMI data" in text
    for label in ("UGL XIX Misiones", "52.4%", "Model context", "Sep 2026", "29,564"):
        assert label in text, label
    for ms in ("12.3 ms", "31.0 ms", "41.5 ms", "36.2 ms", "49.6 ms"):
        assert ms in text, ms
    assert 'style="width:52.4%"' in text
