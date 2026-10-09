"""GATE_AUTONOMOUS=1: every upload reaches a final outcome without a person.

Uncertainty resolves to restriction, never publication. Offline: Guild and AkashML
are stubbed; all PDFs are fictional fixtures.
"""

import json
import time

import pytest

from gate import llm
from test_clearance import NAME, fake_clearance
from test_gate import PDFS, offline_environment, web  # noqa: F401  (fixtures)
from test_learning_flow import BENIGN, BUILTIN_BLOCK, CASE_ID, POSITIVE, SAFE_TEXT, pdf

FIXTURE_NAMES = json.loads((PDFS / "purchases.json").read_text())


@pytest.fixture
def auto(web, monkeypatch):
    monkeypatch.setenv("GATE_AUTONOMOUS", "1")
    return web


def rows(web):
    with web.store.db() as con:
        return [dict(r) for r in con.execute("select * from attachments order by id").fetchall()]


def wait_settled(web, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        current = rows(web)
        if current and not web.app._PENDING and all(r["decision"] != "hold" for r in current):
            return current
        time.sleep(0.05)
    return rows(web)


def all_fixture_names():
    return {name for spec in FIXTURE_NAMES for name in spec["files"]}


def assert_restricted_privately(web, current):
    for row in current:
        assert row["decision"] != "hold"
        if row["decision"] == "withheld":
            assert web.anonymous.get(f"/public/file/{row['id']}").status_code == 404


def test_seeded_fixtures_all_finish_without_a_person(auto):
    assert auto.client.post("/demo/seed", follow_redirects=False).status_code == 303
    current = wait_settled(auto)
    assert {r["filename"] for r in current} == all_fixture_names()
    assert_restricted_privately(auto, current)
    restricted = [r for r in current if any(f["kind"] == "autopilot_restricted" for f in json.loads(r["findings"]))]
    assert restricted
    for row in restricted:
        finding = next(f for f in json.loads(row["findings"]) if f["kind"] == "autopilot_restricted")
        assert finding["severity"] == "review" and finding["rule"] in auto.app.RULES
        assert json.loads(row["reasons"])[-1].startswith("Restricted automatically: ")
        assert row["reviewed_by"] is None
    with auto.store.db() as con:
        logged = con.execute("select count(*) from events where event='autopilot' and actor='autopilot'"
                             " and decision='withheld'").fetchone()[0]
    assert logged == len(restricted)

    portal = auto.anonymous.get("/public")
    assert portal.status_code == 200
    assert "withheld automatically to protect patient data" in portal.text
    assert "awaiting review" not in portal.text.lower() and "en revisión" not in portal.text.lower()
    for name in all_fixture_names():
        assert name not in portal.text
    for spec in FIXTURE_NAMES:
        assert spec["item"] in portal.text  # the purchase record itself is always listed

    activity = auto.client.get("/api/activity").json()
    assert activity["autonomy"] == {"enabled": True, "total": len(current),
                                    "finished": sum(r["decision"] in ("public", "cleaned", "withheld")
                                                    for r in current)}
    assert activity["autonomy"]["finished"] == activity["autonomy"]["total"]
    assert "Finished without a person" in auto.client.get("/live").text


def test_guild_unavailable_restricts_and_never_publishes(auto, monkeypatch):
    monkeypatch.setattr(auto.app.agent, "configured", lambda: True)
    monkeypatch.setattr(auto.app.agent, "clearance", fake_clearance("PASS", 0, error=True))
    monkeypatch.setattr(auto.app.agent, "brief", lambda *a, **k: {"error": "Guild unavailable"})
    monkeypatch.setattr(auto.app.agent, "verify", lambda *a, **k: {"verdict": "ERROR", "text": "unavailable"})
    assert auto.client.post("/demo/seed", follow_redirects=False).status_code == 303
    current = wait_settled(auto)
    assert {r["filename"] for r in current} == all_fixture_names()
    assert_restricted_privately(auto, current)
    assert all(r["decision"] not in ("public", "approved", "cleaned") for r in current)
    assert any(r["decision"] == "withheld" and any(f["kind"] == "autopilot_restricted"
                                                   for f in json.loads(r["findings"])) for r in current)


def test_reviewer_fail_with_clean_candidate_is_restricted(auto, monkeypatch):
    monkeypatch.setattr(auto.app.agent, "configured", lambda: True)
    monkeypatch.setattr(auto.app.agent, "clearance", fake_clearance("FAIL", 3))
    body = (PDFS / "nota_pedido.pdf").read_bytes()
    purchase = auto.app.create_purchase("Synthetic office", "DEMO-AUTO", "Autonomy test", 0)
    att_id = auto.app.store_attachment(purchase, "nota_pedido.pdf", body, *auto.app.evaluate(body))
    deadline = time.time() + 10
    while time.time() < deadline:
        row = next(r for r in rows(auto) if r["id"] == att_id)
        if row["clearance"] and not auto.app._PENDING:
            break
        time.sleep(0.05)
    row = next(r for r in rows(auto) if r["id"] == att_id)
    assert row["decision"] == "withheld"
    assert row["public_pdf"]  # the candidate is kept internally
    served = auto.anonymous.get(f"/public/file/{att_id}")
    assert served.status_code == 404 and NAME.encode() not in served.content
    assert row["public_pdf"] not in served.content


def test_deterministic_block_cannot_be_released_through_review(auto):
    body = pdf(BUILTIN_BLOCK)
    purchase = auto.app.create_purchase("Synthetic office", "DEMO-AUTO", "Block test", 0)
    att_id = auto.app.store_attachment(purchase, "block.pdf", body, *auto.app.evaluate(body))
    row = next(r for r in rows(auto) if r["id"] == att_id)
    assert row["decision"] == "withheld"
    assert not any(f["kind"] == "autopilot_restricted" for f in json.loads(row["findings"]))
    response = auto.client.post(f"/review/{att_id}", data={"action": "approve", "note": "Try to publish a block."},
                                follow_redirects=False)
    assert response.status_code == 409
    assert next(r for r in rows(auto) if r["id"] == att_id)["decision"] == "withheld"
    assert auto.anonymous.get(f"/public/file/{att_id}").status_code == 404


def test_activating_a_rule_restricts_without_a_manual_rescan(auto, monkeypatch):
    learning = auto.app.learning
    monkeypatch.setattr(llm, "review", lambda _text: dict(SAFE_TEXT))
    bodies = {"positive.pdf": pdf(POSITIVE), "benign.pdf": pdf(BENIGN)}
    purchase = auto.app.create_purchase("Synthetic office", "DEMO-AUTO", "Rule test", 0)
    ids = {name: auto.app.store_attachment(purchase, name, body, *auto.app.evaluate(body))
           for name, body in bodies.items()}
    for name, att_id in ids.items():
        served = auto.anonymous.get(f"/public/file/{att_id}")
        assert served.status_code == 200 and served.content == bodies[name]

    called = []
    original = auto.app.rescan_learning_rules
    monkeypatch.setattr(auto.app, "rescan_learning_rules", lambda *a, **k: called.append(1) or original(*a, **k))
    assert auto.client.post(f"/learning/from-case/{CASE_ID}", follow_redirects=False).status_code == 303
    rule = learning.list_rules()[0]
    route = f"/learning/rules/{rule['id']}"
    assert auto.client.post(route + "/test", follow_redirects=False).status_code == 303
    rule = learning.get_rule(rule["id"])
    assert auto.client.post(route + "/activate", data={"digest": rule["digest"]},
                            follow_redirects=False).status_code == 303
    assert not called

    assert auto.anonymous.get(f"/public/file/{ids['positive.pdf']}").status_code == 404
    benign = auto.anonymous.get(f"/public/file/{ids['benign.pdf']}")
    assert benign.status_code == 200 and benign.content == bodies["benign.pdf"]
    positive = next(r for r in rows(auto) if r["id"] == ids["positive.pdf"])
    assert positive["decision"] == "withheld"
    assert all(r["decision"] != "hold" for r in rows(auto))

    # Retiring never releases what the recheck restricted.
    rule = learning.get_rule(rule["id"])
    assert auto.client.post(route + "/retire", data={"digest": rule["digest"]},
                            follow_redirects=False).status_code == 303
    assert auto.anonymous.get(f"/public/file/{ids['positive.pdf']}").status_code == 404
    assert auto.anonymous.get(f"/public/file/{ids['benign.pdf']}").content == bodies["benign.pdf"]


def test_startup_sweep_settles_orphaned_holds(web, monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(llm, "review", lambda _text: None)
        body = pdf(BENIGN)
        purchase = web.app.create_purchase("Synthetic office", "DEMO-AUTO", "Orphan test", 0)
        att_id = web.app.store_attachment(purchase, "orphan.pdf", body, *web.app.evaluate(body))
    assert next(r for r in rows(web) if r["id"] == att_id)["decision"] == "hold"  # flag off: unchanged

    monkeypatch.setenv("GATE_AUTONOMOUS", "1")
    from fastapi.testclient import TestClient
    with TestClient(web.app.app) as restarted:
        assert restarted.get("/public").status_code == 200
    row = next(r for r in rows(web) if r["id"] == att_id)
    assert row["decision"] == "withheld" and row["reviewed_by"] is None
    assert any(f["kind"] == "autopilot_restricted" for f in json.loads(row["findings"]))
    assert web.anonymous.get(f"/public/file/{att_id}").status_code == 404
