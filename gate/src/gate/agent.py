"""Reviewer brief from the Guild-hosted agent.

When the gate holds or withholds a file, the app starts a Guild session with the
masked findings (never the raw document) and stores the agent's brief for the
human reviewer. Guild agents cannot open network connections themselves, so the
app pushes the case in and polls for the answer.

Env: GUILD_KEY_ID, GUILD_KEY_SECRET (API trigger key), GUILD_OWNER, GUILD_WORKSPACE.
"""

import json
import os
import time

import httpx

API = os.getenv("GUILD_API", "https://api.guild.ai/v1")
FINAL = ("DONE", "ERROR", "INTERRUPTED")


def configured() -> bool:
    return all(os.getenv(k) for k in ("GUILD_KEY_ID", "GUILD_KEY_SECRET", "GUILD_OWNER", "GUILD_WORKSPACE"))


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


def _text_from_events(items: list[dict]) -> str:
    """Pull the agent's last text message out of the session events."""
    texts = []
    for ev in items:
        payload = ev.get("data") or ev.get("payload") or ev
        for key in ("text", "content", "message"):
            val = payload.get(key) if isinstance(payload, dict) else None
            if isinstance(val, str) and val.strip():
                texts.append((ev.get("type", ""), val.strip()))
                break
    agent_texts = [t for kind, t in texts if "agent" in kind or "notification" in kind]
    return (agent_texts or [t for _, t in texts] or [""])[-1]


def brief(purchase: dict, filename: str, decision: str, reasons: list[str], findings: list[dict]) -> dict:
    started = time.perf_counter()
    auth = (os.environ["GUILD_KEY_ID"], os.environ["GUILD_KEY_SECRET"])
    url = f"{API}/workspaces/{os.environ['GUILD_OWNER']}/{os.environ['GUILD_WORKSPACE']}/sessions"
    try:
        with httpx.Client(auth=auth, timeout=30) as http:
            session = http.post(url, json={
                "session_type": "api_trigger",
                "agent_input": {"text": case_text(purchase, filename, decision, reasons, findings)},
            })
            session.raise_for_status()
            sid = session.json()["id"]
            status = ""
            for _ in range(60):
                status = http.get(f"{API}/sessions/{sid}").json().get("root_task", {}).get("status", "")
                if status in FINAL:
                    break
                time.sleep(2)
            items = http.get(f"{API}/sessions/{sid}/events", params={"limit": 100}).json()
            items = items.get("items", items) if isinstance(items, dict) else items
            return {"session": sid, "status": status, "text": _text_from_events(items),
                    "latency_ms": (time.perf_counter() - started) * 1000}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"[:300],
                "latency_ms": (time.perf_counter() - started) * 1000}


if __name__ == "__main__":
    # Smoke test: python -m gate.agent
    from dotenv import load_dotenv

    load_dotenv()
    print(json.dumps(brief({"office": "UGL XXX Chivilcoy"}, "especificacion_protesis.pdf", "hold",
                           ["Clinical language without a direct identifier."],
                           [{"severity": "review", "label": "Clinical language", "rule": "health",
                             "evidence": "amputación"}]), indent=2))
