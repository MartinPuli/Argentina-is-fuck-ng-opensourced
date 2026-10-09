"""What the agent is doing right now, step by step, for the live view.

In memory only: the durable record is the attachments table and the audit log.
"""

import os
import threading
import time
from collections import deque

_lock = threading.Lock()
_jobs: deque = deque(maxlen=80)
_feed: deque = deque(maxlen=200)
_local = threading.local()
_next_id = 0
FINISHED = {"done", "skipped", "error"}
# Steps whose error detail can be free text from a model: the feed shows only the verdict.
FREE_TEXT_STEPS = ("Public reviewer", "Guild verifier")


def short(name: str) -> str:
    return name.split("~")[-1].split("/")[-1]


def agent_for(step_name: str) -> str:
    """Who does a step, for the live trace. Names only, never document content."""
    verifier = "Guild · " + short(os.getenv("GUILD_VERIFIER_AGENT", "pami-redaction-verifier"))
    fixed = {
        "Read": "OCR", "Find IDs": "Detectors", "Learned rules": "Detectors", "Decide": "Gate",
        "Clean copy": "Sanitizer",
        "AkashML AI": "AkashML · " + short(os.getenv("AKASHML_MODEL", "gpt-oss-120b")),
        "AkashML vision": "AkashML · " + short(os.getenv("AKASHML_VISION_MODEL", "Qwen3.8-27B")) + " vision",
        "Guild agent note": "Guild · " + short(os.getenv("GUILD_AGENT", "") or "guild-agent"),
        "Guild verifier": verifier, "Clearance levels": "Guild · pami-clearance-orchestrator",
        "Guild orchestrator": "Guild · pami-clearance-orchestrator",
    }
    if step_name in fixed:
        return fixed[step_name]
    if step_name.startswith("Public agent"):
        return "Guild · pami-public-agent"
    if step_name.startswith("Public reviewer"):
        return verifier
    return "Gate"


def _emit(file: str, job_id, agent: str, action: str, status: str = "", detail: str = "",
          duration_ms=None, url: str = "") -> None:
    """Caller holds _lock. Detail must be a category, count, verdict or masked value."""
    event = {"ts": time.time(), "job": job_id, "file": file, "agent": agent, "action": action,
             "status": status, "detail": str(detail)[:120],
             "duration_ms": round(duration_ms) if duration_ms is not None else None}
    if url:
        event["url"] = url
    _feed.append(event)


def emit(job: dict | None, agent: str, action: str, status: str = "", detail: str = "",
         duration_ms=None, url: str = "", file: str = "") -> None:
    with _lock:
        _emit(job["file"] if job else file, job["id"] if job else None, agent, action, status, detail,
              duration_ms, url)


def bind(job: dict | None) -> None:
    """Attach this worker thread to a job, so provider calls deep in the stack can report."""
    _local.job = job


def emit_current(agent: str, action: str, status: str = "", detail: str = "", duration_ms=None,
                 url: str = "") -> None:
    job = getattr(_local, "job", None)
    if job is not None:
        emit(job, agent, action, status, detail, duration_ms, url)


def feed(limit: int = 100) -> list[dict]:
    with _lock:
        return [dict(e) for e in reversed(_feed)][:limit]


def start(purchase: dict, item: str, filename: str, steps: list[str]) -> dict:
    global _next_id
    with _lock:
        _next_id += 1
        job = {
            "id": _next_id, "purchase_id": purchase["id"], "office": purchase["office"],
            "item": item, "file": filename, "attachment_id": None, "decision": None,
            "steps": [{"name": s, "status": "waiting", "detail": "", "agent": agent_for(s),
                       "started_at": None, "ended_at": None, "duration_ms": None} for s in steps],
            "started": time.time(), "done": False,
        }
        _jobs.appendleft(job)
        return job


def step(job: dict, name: str, status: str, detail: str = "") -> None:
    """status: waiting | running | done | skipped | error"""
    with _lock:
        current = next((s for s in job["steps"] if s["name"] == name), None)
        if current is None:
            current = {"name": name, "status": "waiting", "detail": "", "agent": agent_for(name),
                       "started_at": None, "ended_at": None, "duration_ms": None}
            waiting = [i for i, s in enumerate(job["steps"]) if s["status"] == "waiting"]
            job["steps"].insert(waiting[0] if waiting else len(job["steps"]), current)
        was = current["status"]
        current["status"], current["detail"] = status, detail
        now = time.time()
        if status == "running" and was != "running":
            current["started_at"], current["ended_at"], current["duration_ms"] = now, None, None
            _emit(job["file"], job["id"], current["agent"], name, "running")
        elif status in FINISHED and was not in FINISHED:
            if current["started_at"] is None:
                # Finished without a separate start: it ran since the previous step ended.
                ends = [s["ended_at"] for s in job["steps"] if s.get("ended_at")]
                current["started_at"] = max(ends) if ends else job["started"]
            current["ended_at"] = now
            current["duration_ms"] = round((now - current["started_at"]) * 1000)
            shown = "FAIL" if status == "error" and name.startswith(FREE_TEXT_STEPS) else detail
            _emit(job["file"], job["id"], current["agent"], name, status, shown, current["duration_ms"])


def finish(job: dict, **fields) -> None:
    with _lock:
        decision = fields.get("decision")
        if decision and decision != job.get("decision"):
            _emit(job["file"], job["id"], "Gate", "decision", decision, "",
                  (time.time() - job["started"]) * 1000)
        if fields.get("done") and not job.get("done"):
            _emit(job["file"], job["id"], "Gate", "finished", "done", "total", (time.time() - job["started"]) * 1000)
        job.update(fields)


def snapshot() -> list[dict]:
    with _lock:
        return [dict(j, steps=[dict(s) for s in j["steps"]]) for j in _jobs]


def running() -> bool:
    with _lock:
        return any(not j["done"] for j in _jobs)


def clear() -> None:
    """Forget all jobs, for a demo reset between takes."""
    with _lock:
        _jobs.clear()
        _feed.clear()
