"""Reviewer brief from the Guild-hosted agent (guild-agent/PROMPT.md).

When the gate holds or withholds a file, the app opens a Guild session with the
masked findings (never the raw document) and stores the agent's brief for the
human reviewer. Guild agents cannot open network connections themselves, so the
app pushes the case in and polls the session for the answer.

Uses the authenticated `guild` CLI on the host.
Env: GUILD_WORKSPACE (owner~workspace), GUILD_AGENT (owner~agent).
"""

import json
import os
import shutil
import subprocess
import time

POLL_SECONDS = 2
MAX_WAIT_SECONDS = 90


def configured() -> bool:
    return bool(shutil.which("guild") and os.getenv("GUILD_WORKSPACE") and os.getenv("GUILD_AGENT"))


def case_text(purchase: dict, filename: str, decision: str, reasons: list[str], findings: list[dict]) -> str:
    lines = [
        f"Office: {purchase['office']}",
        f"Attachment: {filename}",
        f"Gate decision: {decision}",
        "Reasons: " + " ".join(reasons),
        "Findings (values already masked):",
    ]
    for f in findings:
        lines.append(f"- [{f['severity']}] {f['label']} (rule: {f['rule']}) evidence: {f['evidence']}")
    return "\n".join(lines)


def _guild(*args: str) -> dict:
    out = subprocess.run(["guild", *args], capture_output=True, text=True, timeout=60, check=True)
    return json.loads(out.stdout)


def _reply(session_id: str) -> str:
    items = _guild("session", "events", session_id).get("items", [])
    for ev in reversed(items):
        if ev.get("type") == "agent_notification_message":
            content = ev.get("content") or {}
            return (content.get("data") if isinstance(content, dict) else str(content)) or ""
    return ""


def brief(purchase: dict, filename: str, decision: str, reasons: list[str], findings: list[dict]) -> dict:
    started = time.perf_counter()
    try:
        session = _guild("session", "create", "--workspace", os.environ["GUILD_WORKSPACE"],
                         "--agent", os.environ["GUILD_AGENT"],
                         "--prompt", case_text(purchase, filename, decision, reasons, findings))
        sid = session["id"]
        text = ""
        while not text and time.perf_counter() - started < MAX_WAIT_SECONDS:
            time.sleep(POLL_SECONDS)
            text = _reply(sid)
        return {"session": sid, "url": session.get("session_url", ""), "text": text.strip(),
                "latency_ms": (time.perf_counter() - started) * 1000}
    except Exception as exc:  # the review queue must work without the agent
        return {"error": f"{type(exc).__name__}: {exc}"[:300],
                "latency_ms": (time.perf_counter() - started) * 1000}


if __name__ == "__main__":
    # Smoke test: uv run python -m gate.agent
    from dotenv import load_dotenv

    load_dotenv()
    print(json.dumps(brief({"office": "UGL XXX Chivilcoy"}, "especificacion_protesis.pdf", "hold",
                           ["Clinical language without a direct identifier."],
                           [{"severity": "review", "label": "Clinical language", "rule": "health",
                             "evidence": "amputación"}]), indent=2, ensure_ascii=False))
