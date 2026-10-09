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


VERIFY_WAIT_SECONDS = 90


def verify(text: str, manifest: list[dict]) -> dict:
    """Second, independent agent on Guild: does the cleaned copy still point to a person?

    It receives only the cleaned text, which is what would be published anyway.
    Returns {"verdict": "PASS" | "FAIL" | "ERROR", "text", "url"}.
    """
    started = time.perf_counter()
    removed = ", ".join(sorted({m["category"] for m in manifest})) or "nothing"
    prompt = (f"Removed before publication: {removed}.\n"
              f"Text of the cleaned public copy:\n---\n{text[:6000]}\n---")
    try:
        session = _guild("session", "create", "--workspace", os.environ["GUILD_WORKSPACE"],
                         "--agent", os.getenv("GUILD_VERIFIER_AGENT", "nicopujia~pami-redaction-verifier"),
                         "--prompt", prompt)
        sid, reply = session["id"], ""
        while not reply and time.perf_counter() - started < VERIFY_WAIT_SECONDS:
            time.sleep(POLL_SECONDS)
            reply = _reply(sid)
        reply = reply.strip()
        verdict = "PASS" if reply.upper().startswith("PASS") else "FAIL" if reply else "ERROR"
        return {"verdict": verdict, "text": reply, "url": session.get("session_url", ""),
                "latency_ms": (time.perf_counter() - started) * 1000}
    except Exception as exc:
        return {"verdict": "ERROR", "text": f"{type(exc).__name__}"[:100],
                "latency_ms": (time.perf_counter() - started) * 1000}


# --- Clearance levels: orchestrator -> public agent <-> public reviewer -------------------------

ORCHESTRATOR = "nicopujia~pami-clearance-orchestrator"
PUBLIC_AGENT = "nicopujia~pami-public-agent"
CALL_WAIT_SECONDS = 120
MAX_ROUNDS = 3
CATEGORIES = {"name", "id", "address", "age", "town", "hospital", "date", "diagnosis", "other"}


def _ask(agent_name: str, prompt: str) -> tuple[str, str]:
    """One Guild session; returns (reply, session url). Raises on timeout."""
    started = time.perf_counter()
    session = _guild("session", "create", "--workspace", os.environ["GUILD_WORKSPACE"],
                     "--agent", agent_name, "--prompt", prompt)
    reply = ""
    while not reply and time.perf_counter() - started < CALL_WAIT_SECONDS:
        time.sleep(POLL_SECONDS)
        reply = _reply(session["id"])
    if not reply:
        raise TimeoutError(f"{agent_name} did not answer")
    return reply.strip(), session.get("session_url", "")


def _json(reply: str) -> dict:
    start, end = reply.find("{"), reply.rfind("}")
    data = json.loads(reply[start:end + 1]) if 0 <= start < end else {}
    return data if isinstance(data, dict) else {}


def _spans(items, text: str) -> list[dict]:
    """Keep only exact substrings of the document, so the app can redact them."""
    out, seen = [], set()
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        value = str(item.get("text", "")).strip()
        category = str(item.get("category", "other")).lower()
        if len(value) >= 3 and value in text and value not in seen:
            seen.add(value)
            out.append({"text": value, "category": category if category in CATEGORIES else "other"})
    return out


def _scrub(note: str, spans: list[dict]) -> str:
    for s in spans:
        note = note.replace(s["text"], "[removed]")
    return note[:160]


def _redact_text(text: str, spans: list[dict]) -> str:
    for s in spans:
        text = text.replace(s["text"], " " * len(s["text"]))
    return text


def clearance(text: str, findings: list[dict], render=None, on_step=None) -> dict:
    """Decide what each clearance level may see, with every agent running on Guild.

    The orchestrator classifies each piece of information as clinical, procurement or
    public. The public agent lists the exact text to remove; the app applies it
    (render(remove) -> cleaned text) and the public reviewer checks the result. FAIL
    goes back to the public agent with the feedback, up to MAX_ROUNDS.
    on_step(name, status, detail) reports progress for the live view. Never raises.
    """
    started = time.perf_counter()
    step = on_step or (lambda *a: None)
    render = render or (lambda spans: _redact_text(text, spans))
    sessions, log = [], []
    try:
        masked = "\n".join(f"- {f.get('label', f.get('kind', ''))} ({f.get('severity', '')})" for f in findings)
        step("Guild orchestrator", "running", "")
        reply, url = _ask(ORCHESTRATOR, "MODE: CLASSIFY\nGate findings (masked):\n" + (masked or "- none")
                          + f"\n\nDocument text:\n---\n{text[:8000]}\n---")
        sessions.append({"agent": "orchestrator", "url": url})
        plan = _json(reply)
        classification = [{"item": str(c.get("item", ""))[:80], "level": str(c.get("level", ""))}
                          for c in plan.get("classification", []) if isinstance(c, dict)]
        counts = {lvl: sum(c["level"] == lvl for c in classification) for lvl in ("clinical", "procurement", "public")}
        step("Guild orchestrator", "done", " · ".join(f"{n} {lvl}" for lvl, n in counts.items()))
        procurement = _spans(plan.get("procurement_remove"), text)
        remove = _spans(plan.get("public_hint"), text)
        items = "\n".join(f"- {c['item']}: {c['level']}" for c in classification)

        feedback, verdict, rounds = [], "FAIL", 0
        for rounds in range(1, MAX_ROUNDS + 1):
            name = f"Public agent · round {rounds}"
            step(name, "running", "")
            prompt = (f"Orchestrator classification:\n{items or '- none'}\n\n"
                      + (f"Already removed: {json.dumps(remove, ensure_ascii=False)}\n"
                         f"Reviewer feedback: {feedback[-1]}\n\n" if feedback else "")
                      + f"Document text:\n---\n{text[:8000]}\n---")
            reply, url = _ask(PUBLIC_AGENT, prompt)
            sessions.append({"agent": f"public r{rounds}", "url": url})
            known = {r["text"] for r in remove}
            remove += [s for s in _spans(_json(reply).get("remove"), text) if s["text"] not in known]
            step(name, "done", f"{len(remove)} item(s) to remove")

            review = f"Public reviewer · round {rounds}"
            step(review, "running", "")
            cleaned = render(remove)
            if cleaned is None:
                raise ValueError("cleaned copy could not be built")
            cats = ", ".join(sorted({r["category"] for r in remove})) or "nothing"
            reply, url = _ask(os.getenv("GUILD_VERIFIER_AGENT", "nicopujia~pami-redaction-verifier"),
                              f"Removed before publication: {cats}.\n"
                              f"Text of the cleaned public copy:\n---\n{cleaned[:6000]}\n---")
            sessions.append({"agent": f"reviewer r{rounds}", "url": url})
            verdict = "PASS" if reply.upper().startswith("PASS") else "FAIL"
            note = _scrub(reply, remove)
            log.append({"round": rounds, "removed": len(remove), "review": verdict, "note": note})
            step(review, "done" if verdict == "PASS" else "error", "PASS" if verdict == "PASS" else note[:60])
            if verdict == "PASS":
                break
            feedback.append(note)
        return {"levels": {"public": {"remove": remove, "rounds": rounds, "review": verdict, "feedback": feedback},
                           "procurement": {"remove": procurement}},
                "classification": classification, "sessions": sessions, "log": log,
                "latency_ms": (time.perf_counter() - started) * 1000}
    except Exception as exc:  # the gate must keep working when Guild does not answer
        return {"error": f"{type(exc).__name__}: {exc}"[:200], "sessions": sessions, "log": log,
                "latency_ms": (time.perf_counter() - started) * 1000}


def safe_plan(result: dict) -> dict:
    """The plan without raw phrases: what may be stored and shown."""
    out = {k: v for k, v in result.items() if k != "levels"}
    out["levels"] = {lvl: {**{k: v for k, v in data.items() if k != "remove"},
                           "removed": sorted({r["category"] for r in data.get("remove", [])}),
                           "count": len(data.get("remove", []))}
                     for lvl, data in (result.get("levels") or {}).items()}
    return out
