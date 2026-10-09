"""Guild calls under load and run states, offline: the guild CLI is never executed."""

import subprocess
import threading
import time

import pytest

from gate import activity, agent
from test_activity import live, upload  # noqa: F401  (fixtures)
from test_gate import PDFS, offline_environment, web  # noqa: F401  (fixtures)

ANSWER = {"items": [{"type": "agent_notification_message", "content": {"data": "PASS: nothing identifies"}}]}


def test_poll_timeout_is_retried_not_fatal(monkeypatch):
    calls = []

    def fake_guild(*args):
        calls.append(args)
        if args[:2] == ("session", "create"):
            return {"id": "s1", "session_url": "https://app.guild.ai/sessions/s1"}
        if len(calls) == 2:
            raise subprocess.TimeoutExpired("guild", agent.CLI_TIMEOUT_SECONDS)
        return ANSWER

    monkeypatch.setenv("GUILD_WORKSPACE", "fictional~ws")
    monkeypatch.setattr(agent, "POLL_SECONDS", 0)
    monkeypatch.setattr(agent, "_guild", fake_guild)
    reply, url = agent._ask("fictional~agent", "prompt")
    assert reply.startswith("PASS") and url.endswith("/s1")
    assert len(calls) == 3
    # Only the agent's answers are fetched, never the full event log.
    assert "--events" in calls[1] and "agent_notification_message" in calls[1]


def test_poll_gives_up_only_at_the_overall_deadline(monkeypatch):
    def always_slow(*args):
        if args[:2] == ("session", "create"):
            return {"id": "s1"}
        raise subprocess.TimeoutExpired("guild", 1)

    monkeypatch.setenv("GUILD_WORKSPACE", "fictional~ws")
    monkeypatch.setattr(agent, "POLL_SECONDS", 0)
    monkeypatch.setattr(agent, "CALL_WAIT_SECONDS", 0.2)
    monkeypatch.setattr(agent, "_guild", always_slow)
    with pytest.raises(TimeoutError):
        agent._ask("fictional~agent", "prompt")


def run_failed_clearance(web, monkeypatch, decision):
    def unreachable(*args):
        raise subprocess.TimeoutExpired("guild", agent.CLI_TIMEOUT_SECONDS)

    monkeypatch.setenv("GUILD_WORKSPACE", "fictional~ws")
    monkeypatch.setattr(web.app.agent, "configured", lambda: True)
    monkeypatch.setattr(agent, "_guild", unreachable)
    pdf = (PDFS / "nota_pedido.pdf").read_bytes()
    purchase = web.app.create_purchase("Synthetic office", "DEMO-CLR", "Clearance test", 0)
    job = activity.start(purchase, "Clearance test", "nota_pedido.pdf", [])
    model, _, reasons, findings, latency, revision = web.app.evaluate(pdf)
    web.app.store_attachment(purchase, "nota_pedido.pdf", pdf, model, decision, reasons, findings,
                             latency, revision, job=job)
    deadline = time.time() + 10
    while not job["done"] and time.time() < deadline:
        time.sleep(0.05)
    assert job["done"]
    return job


@pytest.mark.parametrize("decision", ["withheld", "hold"])
def test_failed_clearance_marks_steps_error_and_keeps_a_matching_reason(web, monkeypatch, decision):
    job = run_failed_clearance(web, monkeypatch, decision)
    steps = {s["name"]: s for s in job["steps"]}
    assert steps["Guild orchestrator"]["status"] == "error" and steps["Guild orchestrator"]["detail"]
    assert not any(s["status"] == "running" for s in job["steps"])
    assert job["decision"] == decision
    if decision == "withheld":
        assert "blocking finding" in job["why"] and "must review" not in job["why"]
    else:
        assert "must review" in job["why"]


def test_seed_is_refused_while_a_run_is_in_progress(live):
    entered, release = threading.Event(), threading.Event()
    live.blockers.append(release)
    original = live.app.evaluate

    def slow(data, job=None):
        entered.set()
        assert release.wait(3)
        return original(data, job)

    live.monkeypatch.setattr(live.app, "evaluate", slow)
    assert upload(live).status_code == 303
    assert entered.wait(1)
    response = live.client.post("/live/demo/seed", follow_redirects=False)
    assert response.status_code == 409
    assert len(activity.snapshot()) == 1
    release.set()


def test_public_file_answers_head(web):
    assert web.anonymous.head("/public/file/999999").status_code == 404
