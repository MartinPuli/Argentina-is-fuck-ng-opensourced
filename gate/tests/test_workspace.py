"""Read-only operational metadata, with isolated storage and disabled providers."""

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import dotenv
import pytest
from fastapi.testclient import TestClient

AUTH = ("workspace-reviewer", "fictional-workspace-password")
PRIVATE_MARKER = "PRIVATE-SYNTHETIC-CONTENT-DO-NOT-RETURN"
FILE_FIELDS = {"id", "purchase_id", "filename", "office", "procedure", "decision", "current", "created_at"}


@pytest.fixture
def workspace(monkeypatch, tmp_path):
    # Prevent import-time .env loading from enabling any real provider.
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: False)
    for key in ("AKASHML_API_KEY", "GUILD_WORKSPACE", "GUILD_AGENT", "CLICKHOUSE_HOST"):
        monkeypatch.setenv(key, "")
    monkeypatch.setenv("GATE_STAFF_USERNAME", AUTH[0])
    monkeypatch.setenv("GATE_STAFF_PASSWORD", AUTH[1])
    monkeypatch.setenv("GATE_OPEN_DEMO", "0")
    store = importlib.import_module("gate.store")
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "workspace.sqlite")
    app = importlib.import_module("gate.app")
    learning = importlib.import_module("gate.learning")
    monkeypatch.setattr(app, "events", store.Events())
    with TestClient(app.app) as client:
        yield SimpleNamespace(client=client, app=app, store=store, learning=learning, monkeypatch=monkeypatch)


def add_file(workspace, decision, created_at=1):
    purchase = workspace.app.create_purchase("Fictional office", "SYNTHETIC-2026", "Office chair", 10)
    with workspace.store.db() as con:
        return con.execute(
            "insert into attachments(purchase_id,filename,pdf,decision,findings,model,agent,created_at) "
            "values (?,?,?,?,?,?,?,?)",
            (purchase["id"], f"fictional-{created_at}.pdf", PRIVATE_MARKER.encode(), decision,
             json.dumps([{"evidence": PRIVATE_MARKER}]), json.dumps({"reasons": [PRIVATE_MARKER]}),
             json.dumps({"text": PRIVATE_MARKER}), created_at),
        ).lastrowid


def activate_rule(workspace):
    spec = {"title": "Fictional workspace rule", "groups": [["synthetic sensitive marker"]],
            "action": "hold", "rationale": "Fictional rule fixture", "improvements": [],
            "tests": [{"name": "positive", "text": "synthetic sensitive marker", "should_match": True},
                      {"name": "negative", "text": "ordinary public specification", "should_match": False}]}
    source = {"title": "Fictional source", "url": "https://example.org/fictional",
              "evidence_status": "fictional", "summary": "Local fixture only; no source is fetched."}
    ident = workspace.learning.create_candidate(spec, source, AUTH[0])
    result = workspace.learning.run_tests(ident)
    return workspace.learning.activate(ident, result["digest"], AUTH[0])


@pytest.mark.parametrize("route", ["/", "/api/workspace"])
def test_workspace_requires_configured_identity(workspace, route):
    assert workspace.client.get(route).status_code == 401
    assert workspace.client.get(route, auth=("forged", AUTH[1])).status_code == 401
    workspace.monkeypatch.setenv("GATE_STAFF_PASSWORD", "")
    disabled = workspace.client.get(route, auth=AUTH)
    assert disabled.status_code == 503 and disabled.headers["cache-control"] == "no-store"


def test_home_keeps_the_template_and_authenticated_identity(workspace):
    response = workspace.client.get("/", auth=AUTH)
    assert response.status_code == 200
    assert response.template.name == "home.html"
    assert response.context["user"] == AUTH[0]


def test_empty_workspace_reports_real_zeroes_and_is_not_cacheable(workspace):
    response = workspace.client.get("/api/workspace", auth=AUTH)
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    assert response.json() == {"counts": {"published": 0, "review": 0, "blocked": 0, "stale": 0, "total": 0},
                               "files": []}


def test_counts_follow_actual_current_rules_without_returning_document_bodies(workspace):
    public = add_file(workspace, "public", 1)
    approved = add_file(workspace, "approved", 2)
    held = add_file(workspace, "hold", 3)
    blocked = add_file(workspace, "withheld", 4)
    cleaned = add_file(workspace, "cleaned", 5)
    before = workspace.client.get("/api/workspace", auth=AUTH).json()
    assert before["counts"] == {"published": 3, "review": 1, "blocked": 1, "stale": 0, "total": 5}
    assert before["files"][0]["decision"] == "cleaned" and before["files"][0]["current"] is True
    activate_rule(workspace)
    stale = workspace.client.get("/api/workspace", auth=AUTH).json()
    assert stale["counts"] == {"published": 0, "review": 1, "blocked": 1, "stale": 5, "total": 5}
    workspace.learning.record_check(approved, workspace.learning.revision())
    workspace.learning.record_check(held, workspace.learning.revision())
    workspace.learning.record_check(cleaned, workspace.learning.revision())
    response = workspace.client.get("/api/workspace", auth=AUTH)
    result = response.json()
    assert result["counts"] == {"published": 2, "review": 1, "blocked": 1, "stale": 2, "total": 5}
    current = {row["id"]: row["current"] for row in result["files"]}
    assert current == {public: False, approved: True, held: True, blocked: False, cleaned: True}
    assert all(set(row) == FILE_FIELDS for row in result["files"])
    assert PRIVATE_MARKER not in response.text
    assert all(row["office"] == "Fictional office" and row["procedure"] == "SYNTHETIC-2026"
               for row in result["files"])


def test_recent_files_are_bounded_but_counts_cover_all_attachments(workspace):
    ids = [add_file(workspace, "hold", number) for number in range(105)]
    result = workspace.client.get("/api/workspace", auth=AUTH).json()
    assert result["counts"]["total"] == result["counts"]["review"] == 105
    assert len(result["files"]) == 100
    assert [row["id"] for row in result["files"]] == list(reversed(ids[5:]))


def test_assets_mount_targets_built_frontend_only(workspace):
    mount = next(route for route in workspace.app.app.routes if route.path == "/assets")
    assert mount.name == "assets"
    assert Path(mount.app.directory) == Path(workspace.app.__file__).parent / "static"


def test_server_rendered_documents_work_without_frontend_javascript(workspace):
    add_file(workspace, "hold", 7)
    response = workspace.client.get("/", auth=AUTH)
    assert 'fictional-7.pdf' in response.text
    assert '/purchase/' in response.text and 'Review files' in response.text
    assert 'Loading…' not in response.text
    assert PRIVATE_MARKER not in response.text
    assert response.context['workspace']['counts']['review'] == 1
    activate_rule(workspace)
    stale = workspace.client.get("/", auth=AUTH)
    assert '<td>Recheck</td>' in stale.text
    assert stale.context['workspace']['counts']['published'] == 0


@pytest.mark.parametrize('asset,content_type', [('workspace.js', 'javascript'), ('workspace.css', 'text/css')])
def test_compiled_assets_are_served_in_the_running_application(workspace, asset, content_type):
    response = workspace.client.get('/assets/' + asset)
    assert response.status_code == 200
    assert content_type in response.headers['content-type']
    assert len(response.content) > 1000
