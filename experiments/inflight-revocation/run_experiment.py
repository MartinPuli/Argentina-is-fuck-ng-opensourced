# SPDX-License-Identifier: MIT
"""Independent HTTP client measurements; imports no server authorization decisions."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
import platform
from pathlib import Path
from datetime import datetime, timezone
from gateway import MODES, MAX_BODY, connection, encode, fresh_credentials, request, start_service, stop_services

HERE = Path(__file__).resolve().parent


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def observe(status, raw):
    """Measure actual response body bytes, not controller counters or claimed success."""
    result = {"http_status": status, "body_bytes": len(raw), "body_sha256": digest(raw), "record_ids": [], "protected_line_bytes": 0, "record_bodies": [], "markers": []}
    if status == 200:
        for line in raw.splitlines(keepends=True):
            value = json.loads(line)
            if value.get("type") == "record":
                result["record_ids"].append(value["record"]["id"])
                result["record_bodies"].append(value["record"])
                result["protected_line_bytes"] += len(line)
            else:
                result["markers"].append(value)
    result["record_count"] = len(result["record_ids"])
    return result


def validate_protocol(protocol):
    a, b = protocol["affected_identity"], protocol["independent_identity"]
    reserved = {"gateway_admin", "coordinator", "controller_command"}
    if not isinstance(a, str) or not isinstance(b, str) or a == b or a in reserved or b in reserved:
        raise ValueError("Two distinct unreserved identities are required")
    records = protocol["records"]
    if not 2 <= len(records) <= 128 or len({r["id"] for r in records}) != len(records):
        raise ValueError("Records must be unique and bounded")
    by_id = {r["id"]: r for r in records}
    for key, owner in (("stream_ids", a), ("queued_ids", a), ("legitimate_a_ids", a), ("legitimate_b_ids", b)):
        if not 1 <= len(protocol[key]) <= 64 or any(i not in by_id or by_id[i]["owner"] != owner for i in protocol[key]):
            raise ValueError("Workload records must belong to the declared identity")
    if type(protocol["prefix_chunks"]) is not int or not 1 <= protocol["prefix_chunks"] < len(protocol["stream_ids"]):
        raise ValueError("Stream needs a nonempty prefix and suffix")
    if len(encode(protocol)) > MAX_BODY // 2:
        raise ValueError("Fixture exceeds bound")


def run_case(mode, protocol):
    """Reusable runner. No files written; supports changed IDs, owners, sizes and prefix."""
    validate_protocol(protocol)
    if mode not in MODES:
        raise ValueError("Unknown mode")
    protocol = copy.deepcopy(protocol)
    a, b = protocol["affected_identity"], protocol["independent_identity"]
    tokens = fresh_credentials((a, b))
    processes, stream_conn = [], None
    result = {"mode": mode, "case_id": protocol["case_id"], "workload_sha256": digest(encode(protocol)), "events": [], "observations": {}, "client_pid": os.getpid()}

    def event(name, **details):
        result["events"].append({"order": len(result["events"]) + 1, "event": name, **details})

    def read(name, owner, ids):
        status, raw = request(gateway["origin"], "/read", tokens[owner], {"ids": ids})
        result["observations"][name] = observe(status, raw)
        event(name, http_status=status)

    def sync(path, payload):
        status, raw = request(gateway["origin"], path, tokens["coordinator"], payload)
        if status != 200:
            raise RuntimeError("Synchronization failed: " + str(status))
        return json.loads(raw)

    try:
        process, gateway = start_service("gateway", {"mode": mode, "records": protocol["records"], "identity_tokens": {a: tokens[a], b: tokens[b]}, "gateway_admin": tokens["gateway_admin"], "coordinator": tokens["coordinator"]})
        processes.append(process)
        process, controller = start_service("controller", {"enrolled_identity": a, "gateway_origin": gateway["origin"], "gateway_admin": tokens["gateway_admin"], "command_token": tokens["controller_command"]})
        processes.append(process)
        result["service_pids"] = {"gateway": gateway["pid"], "controller": controller["pid"]}
        # Ports and credentials are deliberately excluded from persisted results.
        read("legitimate_a_before", a, protocol["legitimate_a_ids"])
        read("legitimate_b_before", b, protocol["legitimate_b_ids"])
        status, raw = request(gateway["origin"], "/queue", tokens[a], {"ids": protocol["queued_ids"]})
        if status != 202:
            raise RuntimeError("Queue admission failed")
        job = json.loads(raw)
        event("queue_accepted_before_revocation", http_status=status, state=job["state"])

        stream_conn = connection(gateway["origin"])
        stream_conn.request("POST", "/stream", encode({"ids": protocol["stream_ids"], "stream_id": protocol["stream_id"], "prefix_chunks": protocol["prefix_chunks"]}), {"Authorization": "Bearer " + tokens[a], "Content-Type": "application/json"})
        stream_response = stream_conn.getresponse()
        if stream_response.status != 200:
            raise RuntimeError("Stream admission failed")
        prefix = b""
        for _ in range(protocol["prefix_chunks"]):
            line = stream_response.readline(MAX_BODY + 1)
            if not line.endswith(b"\n") or len(line) > MAX_BODY:
                raise RuntimeError("Incomplete or oversized stream prefix")
            prefix += line
        result["observations"]["stream_before_ack"] = observe(200, prefix)
        event("stream_prefix_received", bytes=len(prefix))
        sync("/sync/wait-stream", {"stream_id": protocol["stream_id"]})
        event("server_pause_confirmed")

        status, raw = request(controller["origin"], "/revoke", tokens["controller_command"], {"identity": a, "expected_generation": 1})
        if status != 200:
            raise RuntimeError("Revocation not acknowledged")
        ack = json.loads(raw)
        if ack.get("gateway_ack", {}).get("revoked") is not True:
            raise RuntimeError("Missing gateway revocation ACK")
        result["revocation_ack"] = ack
        event("controller_ack_received", http_status=status)
        sync("/sync/release-stream", {"stream_id": protocol["stream_id"]})
        event("stream_release_after_ack")
        sync("/sync/release-job", {"job_id": job["job_id"]})
        event("job_release_after_ack")

        suffix = stream_response.read(MAX_BODY + 1)
        if len(suffix) > MAX_BODY:
            raise RuntimeError("Stream suffix exceeds bound")
        result["observations"]["stream_after_ack"] = observe(200, suffix)
        event("stream_suffix_received", bytes=len(suffix))
        stream_conn.close()
        stream_conn = None
        status, raw = request(gateway["origin"], "/job-result", job["ticket"], {"job_id": job["job_id"]})
        result["observations"]["queued_after_ack"] = observe(status, raw)
        event("queued_result_received", http_status=status, bytes=len(raw))
        read("legitimate_a_after", a, protocol["legitimate_a_ids"])
        read("legitimate_b_after", b, protocol["legitimate_b_ids"])
        status, raw = request(controller["origin"], "/revoke", tokens["controller_command"], {"identity": a, "expected_generation": 1})
        result["duplicate_revoke_status"] = status
        event("duplicate_revoke_observed", http_status=status)
        result["metrics"] = summarize(result)
        return result
    finally:
        if stream_conn is not None:
            stream_conn.close()
        result["all_child_processes_stopped"] = stop_services(processes)


def summarize(result):
    obs = result["observations"]
    later = [obs["stream_after_ack"], obs["queued_after_ack"]]
    return {
        "stream_records_received_before_ack": obs["stream_before_ack"]["record_count"],
        "stream_protected_line_bytes_before_ack": obs["stream_before_ack"]["protected_line_bytes"],
        "stream_records_received_after_ack": obs["stream_after_ack"]["record_count"],
        "queued_records_received_after_ack": obs["queued_after_ack"]["record_count"],
        "admitted_operation_records_after_ack": sum(o["record_count"] for o in later),
        "admitted_operation_protected_line_bytes_after_ack": sum(o["protected_line_bytes"] for o in later),
        "admitted_operation_all_body_bytes_after_ack": sum(o["body_bytes"] for o in later),
        "legitimate_a_requests_succeeded": sum(obs[k]["http_status"] == 200 for k in ("legitimate_a_before", "legitimate_a_after")),
        "legitimate_a_requests_attempted": 2,
        "legitimate_b_requests_succeeded": sum(obs[k]["http_status"] == 200 for k in ("legitimate_b_before", "legitimate_b_after")),
        "legitimate_b_requests_attempted": 2,
        "legitimate_b_record_transmissions": sum(obs[k]["record_count"] for k in ("legitimate_b_before", "legitimate_b_after"))
    }


def check_case(result, protocol):
    count = 0
    def check(condition, message):
        nonlocal count
        if not condition:
            raise AssertionError(message)
        count += 1
    obs = result["observations"]
    expected = {r["id"]: r for r in protocol["records"]}
    for name, observation in obs.items():
        for record in observation["record_bodies"]:
            check(record == expected[record["id"]], "Exact fictional record content mismatch: " + name)
        check(observation["record_count"] == len(observation["record_ids"]), "Record count mismatch")
        check(observation["protected_line_bytes"] <= observation["body_bytes"], "Protected byte count exceeds observed body")
    prefix = protocol["prefix_chunks"]
    check(obs["stream_before_ack"]["record_ids"] == protocol["stream_ids"][:prefix], "Declared prefix not observed")
    check(obs["legitimate_a_before"]["record_ids"] == protocol["legitimate_a_ids"], "A initially unavailable")
    check(obs["legitimate_a_after"]["http_status"] == 401, "New A request not rejected")
    for name in ("legitimate_b_before", "legitimate_b_after"):
        check(obs[name]["record_ids"] == protocol["legitimate_b_ids"], "Independent B authority interrupted")
    check(result["duplicate_revoke_status"] == 409, "Duplicate revocation not rejected")
    pids = [result["client_pid"], *result["service_pids"].values()]
    check(len(set(pids)) == 3, "Controller/gateway/client are not separate processes")
    check(result["all_child_processes_stopped"], "Leaked child process")
    events = {e["event"]: e["order"] for e in result["events"]}
    check(events["queue_accepted_before_revocation"] < events["controller_ack_received"] < events["job_release_after_ack"] < events["queued_result_received"], "Queue ordering invalid")
    check(events["stream_prefix_received"] < events["server_pause_confirmed"] < events["controller_ack_received"] < events["stream_release_after_ack"] < events["stream_suffix_received"], "Stream ordering invalid")
    if result["mode"] == "entry_only":
        check(obs["stream_after_ack"]["record_ids"] == protocol["stream_ids"][prefix:], "Entry-only stream not completed")
        check(obs["queued_after_ack"]["record_ids"] == protocol["queued_ids"], "Entry-only queued job not completed")
    else:
        for name in ("stream_after_ack", "queued_after_ack"):
            check(obs[name]["record_count"] == 0, "Revoked generation released protected records")
            check(obs[name]["protected_line_bytes"] == 0, "Revoked generation released protected line bytes")
            check(obs[name]["markers"] == [{"type": "denied", "reason": "admitted_generation_revoked"}], "Missing explicit denial")
    return count


def source_hashes():
    return {name: digest((HERE / name).read_bytes()) for name in ("gateway.py", "run_experiment.py", "protocol.json", "PLAN.md")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=HERE / "protocol.json")
    parser.add_argument("--output", type=Path, default=HERE / "results.json")
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text())
    runs = [run_case(mode, protocol) for mode in MODES]
    assertions = sum(check_case(run, protocol) for run in runs)
    if runs[0]["workload_sha256"] != runs[1]["workload_sha256"]:
        raise AssertionError("Workloads differ")
    assertions += 1
    output = {"experiment": "inflight-revocation", "license": "CC BY 4.0 (results); MIT (code/fixtures)", "created_at_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(), "source_hashes": source_hashes(), "protocol_file_sha256": digest(args.protocol.read_bytes()), "assertions_passed": assertions, "runs": runs, "claims": {"actual_loopback_http": True, "deterministic_barrier_ordering": True, "paper_reproduction": False, "detection_evaluated": False, "sandbox_security_evaluated": False, "durable_revocation_evaluated": False, "latency_measured": False}}
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"assertions_passed": assertions, "runs": [{"mode": r["mode"], **r["metrics"]} for r in runs]}, indent=2))


if __name__ == "__main__":
    main()
