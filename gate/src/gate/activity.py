"""What the agent is doing right now, step by step, for the live view.

In memory only: the durable record is the attachments table and the audit log.
"""

import threading
import time
from collections import deque

_lock = threading.Lock()
_jobs: deque = deque(maxlen=80)
_next_id = 0


def start(purchase: dict, item: str, filename: str, steps: list[str]) -> dict:
    global _next_id
    with _lock:
        _next_id += 1
        job = {
            "id": _next_id, "purchase_id": purchase["id"], "office": purchase["office"],
            "item": item, "file": filename, "attachment_id": None, "decision": None,
            "steps": [{"name": s, "status": "waiting", "detail": ""} for s in steps],
            "started": time.time(), "done": False,
        }
        _jobs.appendleft(job)
        return job


def step(job: dict, name: str, status: str, detail: str = "") -> None:
    """status: waiting | running | done | skipped | error"""
    with _lock:
        for s in job["steps"]:
            if s["name"] == name:
                s["status"], s["detail"] = status, detail
                return
        new = {"name": name, "status": status, "detail": detail}
        waiting = [i for i, s in enumerate(job["steps"]) if s["status"] == "waiting"]
        job["steps"].insert(waiting[0] if waiting else len(job["steps"]), new)


def finish(job: dict, **fields) -> None:
    with _lock:
        job.update(fields)


def snapshot() -> list[dict]:
    with _lock:
        return [dict(j, steps=[dict(s) for s in j["steps"]]) for j in _jobs]
