# SPDX-License-Identifier: MIT
"""Independent sequential client. Only main() writes the named result files."""
import copy
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import re
import secrets

from services import (MODES, canonical, check_bind, digest, observer_process,
                      request, sanitized_exposure, serve)

HERE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def validate(protocol, workload):
    check_bind(protocol["bind"])
    require(protocol["enrolled_identity"] == "A", "This fixture enrolls identity A")
    require(set(protocol["permissions"]) == {"A", "B"}, "Expected A/B identities")
    route = protocol["exposure_route"]
    require(isinstance(route, str) and re.fullmatch(r"/[A-Za-z0-9_./-]+", route)
            and not route.startswith(("//", "/control/")) and route != "/use", "Invalid fixture route")
    records = protocol["records"]
    require(0 < len(records) <= 1000, "Expected bounded fictional records")
    require(len({r["id"] for r in records}) == len(records), "Duplicate record IDs")
    for r in records:
        require(set(r) == {"id", "owner"} and all(isinstance(v, str) for v in r.values()), "Record shape")
    require(len({e["id"] for e in workload["events"]}) == len(workload["events"]), "Duplicate event IDs")


def recv(pipe):
    if not pipe.poll(15):
        raise RuntimeError("Child did not respond; no evidence of success")
    return pipe.recv()


def stop_services(processes):
    """Stop only explicitly supplied experiment child processes."""
    for process in reversed(processes):
        if process.is_alive():
            process.terminate()
        process.join(timeout=5)
        if process.is_alive():
            process.kill()
            process.join(timeout=5)


def start_service(kind, config, context=None):
    """Return (child process, origin/pid metadata); caller must stop the process."""
    check_bind(config["bind"])
    context = context or multiprocessing.get_context("spawn")
    parent, child = context.Pipe()
    process = context.Process(target=serve, args=(kind, config, child), name="fixture-" + kind)
    process.start()
    child.close()
    try:
        return process, recv(parent)
    except Exception:
        stop_services([process])
        raise
    finally:
        parent.close()


def summarize(transcript):
    """Derive counts only from independent client HTTP bodies, never service counters."""
    groups = {}
    for event in transcript:
        if event["op"] != "read":
            continue
        label = event["label"]
        bucket = groups.setdefault(label, {"requests": 0, "completed": 0, "denied": 0,
                                          "record_transmissions": 0, "distinct_ids": set(),
                                          "after_first_response_records": 0})
        bucket["requests"] += 1
        response = event["response"]
        bucket["completed"] += int(response["status"] == 200)
        bucket["denied"] += int(response["status"] != 200)
        ids = [r["id"] for r in response["body"].get("records", [])]
        bucket["record_transmissions"] += len(ids)
        bucket["distinct_ids"].update(ids)
        if event["after_first_response"]:
            bucket["after_first_response_records"] += len(ids)
    for bucket in groups.values():
        bucket["distinct_ids"] = sorted(bucket["distinct_ids"])
        bucket["distinct_record_count"] = len(bucket["distinct_ids"])
    return groups


def run_mode(mode, protocol, workload):
    """Generic synchronous runner; no writes, assertions of main-case effects or remote access."""
    validate(protocol, workload)
    require(mode in MODES, "Unknown mode")
    context = multiprocessing.get_context("spawn")
    children, endpoints, pids = [], {}, {"verifier": os.getpid()}
    tokens = {k: secrets.token_urlsafe(32) for k in
              ("A", "B", "gateway_admin", "app_admin", "app_client", "observer", "recovery")}
    secrets_seen = list(tokens.values())
    stolen, captured_bodies, evidence = {}, {}, None
    trace, responded = [], False

    def start(kind, config):
        process, info = start_service(kind, config, context)
        children.append(process)
        endpoints[kind], pids[kind] = info["origin"], info["pid"]
        return info["origin"]

    observer_pipe = None
    try:
        gateway = start("gateway", {"bind": protocol["bind"], "protocol": protocol,
                        "tokens": {"A": tokens["A"], "B": tokens["B"]}, "admin": tokens["gateway_admin"]})
        app = start("app", {"bind": protocol["bind"], "identity": "A", "route": protocol["exposure_route"],
                    "gateway": gateway, "credential": tokens["A"], "client": tokens["app_client"],
                    "admin": tokens["app_admin"]})
        controller = start("controller", {"bind": protocol["bind"], "mode": mode, "identity": "A",
                           "route": protocol["exposure_route"], "app": app, "gateway": gateway,
                           "app_admin": tokens["app_admin"], "gateway_admin": tokens["gateway_admin"],
                           "observer": tokens["observer"], "recovery": tokens["recovery"]})
        observer_pipe, child = context.Pipe()
        process = context.Process(target=observer_process, args=({"app": app, "controller": controller,
                                  "route": protocol["exposure_route"], "identity": "A",
                                  "observer": tokens["observer"]}, child), name="fixture-observer")
        process.start()
        child.close()
        children.append(process)
        pids["observer"] = recv(observer_pipe)["pid"]

        def claim_from_capture(event_id):
            body = captured_bodies["stolen_initial"]
            return {"observation_id": event_id, "target": "A", "origin": app,
                    "route": protocol["exposure_route"], "generation": body["generation"],
                    "fingerprint": digest(stolen["stolen_initial"])}

        for event in workload["events"]:
            item = {"id": event["id"], "op": event["op"]}
            op = event["op"]
            if op == "capture":
                response = request(app, "GET", protocol["exposure_route"])
                item["response"] = sanitized_exposure(response)
                token = response["body"].get("credential") if response["status"] == 200 else None
                if token:
                    stolen[event["slot"]] = token
                    captured_bodies[event["slot"]] = response["body"]
                    secrets_seen.append(token)
                item["credential_acquired"] = bool(token)
            elif op == "read":
                ids = [r["id"] for r in protocol["records"]] if event["ids"] == "all" else event["ids"]
                if event["via"] == "app":
                    response = request(app, "POST", "/use", {"ids": ids}, tokens["app_client"])
                    acquired = True
                else:
                    alias = event["credential"]
                    token = tokens["B"] if alias == "B" else stolen.get(alias)
                    acquired = bool(token)
                    response = request(gateway, "POST", "/records", {"ids": ids}, token)
                received = response["body"].get("records", [])
                manifest = {r["id"]: r for r in protocol["records"]}
                require(isinstance(received, list) and all(isinstance(r, dict) and
                        r.get("id") in manifest and r == manifest[r["id"]] for r in received),
                        "Unrecognized actual response record")
                require(response["status"] == 200 or not received, "Failed response released records")
                item.update(response=response, label=event["label"], requested_ids=ids,
                            credential_available=acquired, after_first_response=responded)
            elif op == "claim":
                body = claim_from_capture(event["id"])
                variant = event["variant"]
                authorization = tokens["observer"]
                if variant == "false_digest":
                    body["fingerprint"] = "0" * 64
                elif variant == "wrong_target":
                    body["target"] = "B"
                elif variant == "wrong_origin":
                    body["origin"] = "http://127.0.0.1:1"
                elif variant == "unauthenticated":
                    authorization = None
                else:
                    raise ValueError("Unknown claim variant")
                item["response"] = request(controller, "POST", "/evidence", body, authorization)
            elif op == "observe":
                observer_pipe.send({"observation_id": event["id"]})
                observation = recv(observer_pipe)
                require("error" not in observation, "Observer failed")
                item["observation"] = observation
                if evidence is None and observation["evidence"]:
                    evidence = observation["evidence"]
                if observation["controller"] and observation["controller"]["status"] == 200:
                    responded = True
            elif op == "replay":
                require(evidence is not None, "Replay requires actual prior observer evidence")
                body = copy.deepcopy(evidence)
                if event["variant"] == "conflict":
                    body["fingerprint"] = "f" * 64
                elif event["variant"] == "stale":
                    body["observation_id"] = event["id"]
                elif event["variant"] != "same":
                    raise ValueError("Unknown replay variant")
                item["response"] = request(controller, "POST", "/evidence", body, tokens["observer"])
            elif op == "recover":
                item["response"] = request(controller, "POST", "/recover",
                                           {"operation_id": event["id"],
                                            "expected_generation": event["expected_generation"]}, tokens["recovery"])
            else:
                raise ValueError("Unknown workload operation")
            trace.append(item)
        result = {"mode": mode, "process_ids": pids, "endpoints": endpoints,
                  "protocol_sha256": hashlib.sha256(canonical(protocol)).hexdigest(),
                  "workload_sha256": hashlib.sha256(canonical(workload)).hexdigest(),
                  "transcript": trace, "metrics": summarize(trace)}
        serialized = json.dumps(result, sort_keys=True)
        require(all(value not in serialized for value in secrets_seen), "Credential persistence prevented")
        return result
    finally:
        if observer_pipe is not None:
            observer_pipe.close()
        stop_services(children)


def verify(results):
    """Fixed main-case expectations; independent variants should supply their own checks."""
    checks = []

    def check(name, condition):
        require(condition, name)
        checks.append({"name": name, "passed": True})

    expected = {"scope_only": (6, 3, 4), "repair_only": (5, 2, 4),
                "revoke_only": (4, 1, 2), "combined": (3, 0, 3)}
    for result in results:
        mode, stats = result["mode"], result["metrics"]
        events = {e["id"]: e for e in result["transcript"]}
        check(mode + ": distinct processes", len(set(result["process_ids"].values())) == 5)
        total, after, a_completed = expected[mode]
        check(mode + ": actual misuse transmissions", stats["misuse"]["record_transmissions"] == total)
        check(mode + ": actual post-response transmissions", stats["misuse"]["after_first_response_records"] == after)
        check(mode + ": A availability measured", stats["legitimate_A"]["completed"] == a_completed
              and stats["legitimate_A"]["requests"] == 4)
        check(mode + ": B batch continuity", stats["legitimate_B"]["completed"] == 3
              and stats["legitimate_B"]["record_transmissions"] == 36)
        check(mode + ": owner scope", stats["cross_owner"]["completed"] == 0
              and stats["cross_owner"]["record_transmissions"] == 0)
        for event_id, status in (("false_claim", 422), ("wrong_target", 403), ("wrong_origin", 403),
                                 ("unauthenticated_claim", 401), ("conflicting_response", 409),
                                 ("stale_generation", 409)):
            check(mode + ": " + event_id, events[event_id]["response"]["status"] == status)
        observation = events["observe_response"]["observation"]
        check(mode + ": observer and controller read exposure", observation["observation"]["status"] == 200
              and observation["controller"]["body"].get("corroboration_http_status") == 200)
        for event_id in ("duplicate_response", "duplicate_after_replacement"):
            check(mode + ": " + event_id, events[event_id]["response"]["body"].get("duplicate") is True)
        check(mode + ": replacement provisioned", events["replacement"]["response"]["body"].get("generation") == 2)
        check(mode + ": replacement works after stale/duplicate commands", events["a_recovered"]["response"]["status"] == 200)
        repaired = mode in ("repair_only", "combined")
        revoked = mode in ("revoke_only", "combined")
        check(mode + ": exposure route repair", events["capture_replacement"]["response"]["status"] == (404 if repaired else 200))
        check(mode + ": old credential state", events["misuse_original_late"]["response"]["status"] == (401 if revoked else 200))
        check(mode + ": stolen replacement counterexample", events["misuse_replacement"]["response"]["status"] == (401 if repaired else 200))
        check(mode + ": final A state measured", events["a_after_second_observation"]["response"]["status"] == (401 if mode == "revoke_only" else 200))
    for host in ("0.0.0.0", "::1", "localhost", "192.0.2.1"):
        try:
            check_bind(host)
        except ValueError:
            check("refuse bind " + host, True)
        else:
            check("refuse bind " + host, False)
    return checks


def main():
    protocol = json.loads((HERE / "protocol.json").read_text())
    workload = json.loads((HERE / "workload.json").read_text())
    results = [run_mode(mode, protocol, workload) for mode in protocol["modes"]]
    checks = verify(results)
    sources = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
               for name in ("services.py", "run_experiment.py", "protocol.json", "workload.json", "PLAN.md")}
    document = {"license": "CC-BY-4.0", "schema_version": 1, "source_sha256": sources,
                "protocol": protocol, "workload": workload, "results": results, "checks": checks,
                "timing": "Sequential requests; no detection or containment latency measured."}
    summary = {"license": "CC-BY-4.0", "source_sha256": sources, "checks_passed": len(checks),
               "metrics": {r["mode"]: r["metrics"] for r in results}}
    for name, data in (("results.json", document), ("summary.json", summary)):
        (HERE / name).write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({"checks_passed": len(checks), "metrics": summary["metrics"]}, indent=2))


if __name__ == "__main__":
    main()
