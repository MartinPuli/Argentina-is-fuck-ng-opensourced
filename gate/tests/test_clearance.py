"""Clearance levels through Guild, offline: agent.clearance is replaced by a fake."""

import json
import time

import pytest

from test_gate import PDFS, offline_environment, web  # noqa: F401  (fixtures)

NAME = "Juana Ficticia Pérez"


def run(web, monkeypatch, fake):
    monkeypatch.setattr(web.app.agent, "configured", lambda: True)
    monkeypatch.setattr(web.app.agent, "clearance", fake)
    pdf = (PDFS / "nota_pedido.pdf").read_bytes()
    purchase = web.app.create_purchase("Synthetic office", "DEMO-CLR", "Clearance test", 0)
    att_id = web.app.store_attachment(purchase, "nota_pedido.pdf", pdf, *web.app.evaluate(pdf))
    deadline = time.time() + 10
    while time.time() < deadline:
        with web.store.db() as con:
            row = con.execute("select * from attachments where id=?", (att_id,)).fetchone()
        if row["clearance"] or row["decision"] in ("cleaned", "hold") and fake.done:
            break
        time.sleep(0.05)
    time.sleep(0.1)
    with web.store.db() as con:
        return att_id, pdf, con.execute("select * from attachments where id=?", (att_id,)).fetchone()


def fake_clearance(review, rounds, error=False):
    def fake(text, findings, render=None, on_step=None):
        fake.done = True
        if error:
            return {"error": "TimeoutError: no answer", "sessions": [], "log": []}
        remove = [{"text": NAME, "category": "name"}]
        assert NAME in text
        cleaned = render(remove)
        assert cleaned is not None and NAME not in cleaned
        return {"levels": {"public": {"remove": remove, "rounds": rounds, "review": review,
                                      "feedback": [] if review == "PASS" else ["FAIL: still identifies"] * rounds},
                           "procurement": {"remove": remove}},
                "classification": [{"item": "patient name", "level": "clinical"}],
                "sessions": [{"agent": "orchestrator", "url": "https://app.guild.ai/sessions/x"}],
                "log": [], "latency_ms": 1.0}
    fake.done = False
    return fake


def test_review_pass_publishes_the_cleaned_copy(web, monkeypatch):
    att_id, original, row = run(web, monkeypatch, fake_clearance("PASS", 1))
    assert row["decision"] == "cleaned"
    plan = json.loads(row["clearance"])
    assert plan["levels"]["public"]["review"] == "PASS" and plan["levels"]["public"]["removed"] == ["name"]
    assert NAME not in row["clearance"]  # the stored plan never carries raw phrases
    served = web.anonymous.get(f"/public/file/{att_id}")
    assert served.status_code == 200
    assert served.content == row["public_pdf"] and served.content != original
    assert web.client.get(f"/internal/procurement/{att_id}").content == row["procurement_pdf"]
    assert web.anonymous.get(f"/internal/procurement/{att_id}").status_code == 401


def test_review_fail_after_three_rounds_holds(web, monkeypatch):
    att_id, _, row = run(web, monkeypatch, fake_clearance("FAIL", 3))
    assert row["decision"] == "hold"
    assert row["public_pdf"]  # the cleaned copy is kept for a human
    assert json.loads(row["clearance"])["levels"]["public"]["rounds"] == 3
    assert web.anonymous.get(f"/public/file/{att_id}").status_code == 404


def test_clearance_error_keeps_the_file_private(web, monkeypatch):
    att_id, _, row = run(web, monkeypatch, fake_clearance("PASS", 0, error=True))
    assert row["decision"] not in ("cleaned", "public", "approved")
    assert "error" in json.loads(row["clearance"])
    assert web.anonymous.get(f"/public/file/{att_id}").status_code == 404


@pytest.mark.parametrize("reply", ['{"remove": [{"text": "Juana Ficticia Pérez", "category": "name"},'
                                   ' {"text": "not in the document", "category": "name"}]}'])
def test_agent_spans_keep_only_exact_substrings(reply):
    from gate import agent
    spans = agent._spans(agent._json("noise " + reply).get("remove"), f"Beneficiaria: {NAME} - DNI")
    assert spans == [{"text": NAME, "category": "name"}]


def test_purchase_page_shows_the_guild_reviewer_verdict(web):
    from test_gate import CLEANED, MANIFEST, add_attachment
    att_id, _ = add_attachment(web, "cleaned", CLEANED, MANIFEST)
    plan = web.app.agent.safe_plan({
        "levels": {"public": {"remove": [{"text": NAME, "category": "name"}], "rounds": 2, "review": "PASS",
                              "feedback": ["FAIL: still identifies"]}},
        "sessions": [{"agent": "orchestrator", "url": "https://app.guild.ai/sessions/orch"},
                     {"agent": "reviewer r1", "url": "https://app.guild.ai/sessions/rev1"},
                     {"agent": "reviewer r2", "url": "https://app.guild.ai/sessions/rev2"}],
        "log": [], "latency_ms": 1.0})
    with web.store.db() as con:  # stored exactly as clearance_in_background stores it
        con.execute("update attachments set clearance=? where id=?", (json.dumps(plan), att_id))
        pid = con.execute("select purchase_id from attachments where id=?", (att_id,)).fetchone()[0]
    page = web.client.get(f"/purchase/{pid}").text
    assert "Verified · Guild reviewer PASS (round 2)" in page
    assert "https://app.guild.ai/sessions/rev2" in page
    assert "Not verified" not in page
