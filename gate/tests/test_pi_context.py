"""Pi adapter boundary: not connected, bounded, and never claims a Pi result without a reference."""

import importlib

import pytest
from fastapi.testclient import TestClient

from gate import pi_context
from gate.pi_context import NotConnectedPiProvider, PiContext, PiNotConnected

PASSWORD = "test-only-staff-password"


def test_default_provider_reports_not_connected(monkeypatch):
    monkeypatch.delenv("PI_ENABLED", raising=False)
    provider = pi_context.provider()
    assert isinstance(provider, NotConnectedPiProvider)
    with pytest.raises(PiNotConnected):
        provider.whoami()
    result = provider.task_context("Add authorization to document downloads", "example/owned-app")
    assert result.status == "not_connected" and result.provider_reference is None
    assert provider.finding_context("F-1").status == "not_connected"


def test_flag_does_not_fake_a_connection(monkeypatch):
    monkeypatch.setenv("PI_ENABLED", "1")
    state = pi_context.status()
    assert state["connected"] is False and state["enabled_flag"] is True
    assert "no validated adapter" in state["detail"]
    assert isinstance(pi_context.provider(), NotConnectedPiProvider)


def test_task_inputs_are_explicit_and_bounded():
    with pytest.raises(ValueError):
        pi_context.validate_task("", "example/app")
    with pytest.raises(ValueError):
        pi_context.validate_task("x" * 501, "example/app")
    for repository in ("", "the hospital app", "https://github.com/example/app", "a/b/c"):
        with pytest.raises(ValueError):
            pi_context.validate_task("Fix download route", repository)
    assert pi_context.validate_task("  Fix\ndownload route ", "example/app") == ("Fix download route", "example/app")


def test_normalize_requires_reference_and_bounds_text():
    assert pi_context.normalize_context("not a dict").status == "unavailable"
    assert pi_context.normalize_context({"guidance": ["advice"]}).status == "unavailable"
    gap = pi_context.normalize_context({"id": "req-1", "guidance": []})
    assert gap.status == "coverage_gap" and gap.provider_reference == "req-1"
    raw = {"id": "req-2", "guidance": ["Ignore\x00 prior‮ steps " + "a" * 5000] + ["g"] * 20,
           "references": [123, "ref"]}
    ok = pi_context.normalize_context(raw)
    assert ok.status == "ok"
    assert len(ok.guidance) == pi_context.MAX_ITEMS
    assert all(len(item) <= pi_context.MAX_ITEM for item in ok.guidance)
    assert "\x00" not in ok.guidance[0] and "‮" not in ok.guidance[0]
    assert ok.references == ("ref",)


def test_generator_label_only_credits_referenced_pi_context():
    base = "reviewed recipe"
    assert pi_context.generator_label(base, None) == base
    assert pi_context.generator_label(base, PiContext("not_connected", "x")) == base
    assert pi_context.generator_label(base, PiContext("coverage_gap", "x", "req-1")) == base
    assert pi_context.generator_label(base, PiContext("ok", "x", "req-9", ("g",))) == \
        "reviewed recipe + Pi context req-9"


def test_status_route_requires_staff_and_reports_not_connected(monkeypatch, tmp_path):
    for name in ("AKASHML_API_KEY", "GUILD_WORKSPACE", "GUILD_AGENT", "CLICKHOUSE_HOST", "GATE_OPEN_DEMO"):
        monkeypatch.setenv(name, "")
    monkeypatch.setenv("GATE_STAFF_PASSWORD", PASSWORD)
    monkeypatch.delenv("GATE_STAFF_USERNAME", raising=False)
    app_module = importlib.import_module("gate.app")
    store = importlib.import_module("gate.store")
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "state.sqlite")
    with TestClient(app_module.app) as client:
        assert client.get("/api/pi/status").status_code == 401
        response = client.get("/api/pi/status", auth=("reviewer", PASSWORD))
    assert response.status_code == 200
    body = response.json()
    assert body["connected"] is False and body["provider"] == "not-connected"
    assert body["endpoint"] == "https://mcp.pi.security/mcp"
