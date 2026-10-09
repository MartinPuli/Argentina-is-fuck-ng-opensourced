# SPDX-License-Identifier: MIT
"""Run the synthetic HTTP workload and score actual client-observed response bodies."""
import hashlib
import json
import secrets
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener

BASE = Path(__file__).resolve().parent
MODES = ("no_containment", "naive_volume", "scope_only", "scope_and_revocation")
OPENER = build_opener(ProxyHandler({}))  # Never route loopback traffic to an environment proxy.


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def http(port, path, token=None, payload=None):
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = "Bearer " + token
    request = Request(f"http://127.0.0.1:{port}{path}",
                      data=None if payload is None else json.dumps(payload).encode(), headers=headers)
    try:
        response = OPENER.open(request, timeout=5)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read()
        return {"status": response.status, "body": json.loads(raw), "body_sha256": hashlib.sha256(raw).hexdigest(),
                "body_bytes": len(raw)}


def public_response(response):
    copy = json.loads(json.dumps(response))
    if "credential" in copy["body"]:
        copy["body"]["credential"] = "[REDACTED: fresh synthetic credential]"
    return copy


def command_payload(contract, command_id, identity, action, tick, generation, ttl=10):
    return {"command_id": command_id, "identity": identity, "action": action,
            "issued_at": tick, "expires_at": tick + ttl, "expected_generation": generation,
            "contract_digest": digest(contract)}


def observe_records(response, expected_record_ids):
    # No exposure counters are fetched from the service or controller.
    records = response["body"].get("records", [])
    if not isinstance(records, list):
        raise AssertionError("Malformed record response")
    delivered = [record["id"] for record in records]
    if any(record_id not in expected_record_ids for record_id in delivered):
        raise AssertionError("Service returned a record outside the fictional manifest")
    if response["status"] != 200 and delivered:
        raise AssertionError("Denied response leaked records")
    return delivered


def summarize(observations):
    reads = [item for item in observations if item["event"]["kind"] == "read"]
    order = {id(item): index for index, item in enumerate(observations)}
    confirmation_index = next(index for index, item in enumerate(observations) if item["event"]["kind"] == "confirmed_compromise")
    replacement_index = next(index for index, item in enumerate(observations) if item["event"]["kind"] == "issue_replacement")
    output = {}
    groups = {
        "all_reads": reads,
        "legitimate": [item for item in reads if item["event"]["intent"] == "legitimate"],
        "A_legitimate": [item for item in reads if item["event"]["intent"] == "legitimate" and item["event"]["credential"].startswith("A-")],
        "B_authorized_batch": [item for item in reads if item["event"]["credential"] == "B-original"],
        "credential_misuse": [item for item in reads if item["event"]["intent"] == "credential_misuse"],
        "scope_probes": [item for item in reads if item["event"]["intent"] == "unauthorized_scope_probe"],
        "misuse_before_confirmation": [item for item in reads if item["event"]["intent"] == "credential_misuse" and order[id(item)] < confirmation_index],
        "misuse_after_confirmation": [item for item in reads if item["event"]["intent"] == "credential_misuse" and order[id(item)] > confirmation_index],
        "original_after_replacement": [item for item in reads if item["event"]["credential"] == "A-original" and order[id(item)] > replacement_index],
    }
    for group, items in groups.items():
        delivered = [record_id for item in items for record_id in item["delivered_record_ids"]]
        output[group] = {"requests": len(items), "http_200": sum(item["response"]["status"] == 200 for item in items),
                         "record_transmissions": len(delivered), "unique_records_delivered": len(set(delivered)),
                         "unique_record_ids": sorted(set(delivered))}
    return output


def run_mode(mode, contract, workload):
    confirmation_tick = next(event["tick"] for event in workload["events"] if event["kind"] == "confirmed_compromise")
    replacement_tick = next(event["tick"] for event in workload["events"] if event["kind"] == "issue_replacement")
    control_secret = secrets.token_urlsafe(32)
    credentials = {"A-original": secrets.token_urlsafe(32), "B-original": secrets.token_urlsafe(32)}
    config = {"host": "127.0.0.1", "mode": mode, "contract": contract, "control_secret": control_secret,
              "initial_credentials": {"A": credentials["A-original"], "B": credentials["B-original"]}}
    process = subprocess.Popen([sys.executable, str(BASE / "service.py")], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    observations = []
    record_ids = {f"{owner}-{n:02}" for owner in contract["owners"] for n in range(1, contract["records_per_owner"] + 1)}
    revoke = None
    replacement_command = None
    try:
        process.stdin.write(json.dumps(config) + "\n")
        process.stdin.flush()
        startup = process.stdout.readline()
        if not startup:
            raise RuntimeError("Local service could not start: " + process.stderr.read())
        ports = json.loads(startup)
        # Demonstrate that a data credential cannot authorize control-plane mutation.
        control_probe = http(ports["control"], "/clock", credentials["A-original"], {"tick": 100})
        if control_probe["status"] != 401:
            raise AssertionError("Data credential gained control-plane authority")
        for event in workload["events"]:
            tick = event["tick"]
            clock = http(ports["control"], "/clock", control_secret, {"tick": tick})
            if clock["status"] != 200:
                raise AssertionError("Controller clock did not advance")
            kind = event["kind"]
            observation = {"event": event}
            if kind == "read":
                query = [("owner", event["owner"])] + [("id", value) for value in event.get("record_ids", [])]
                response = http(ports["data"], "/records?" + urlencode(query), credentials[event["credential"]])
                observation["delivered_record_ids"] = observe_records(response, record_ids)
            elif kind == "telemetry":
                response = http(ports["data"], "/telemetry", payload={"text": event["text"]})
            elif kind == "confirmed_compromise":
                # This event is supplied by the scenario authority, NOT inferred from traffic or a log string.
                if mode == "scope_and_revocation":
                    revoke = command_payload(contract, "revoke-A-v1", event["identity"], "revoke_credential", tick, 1)
                    revoke["source_event_id"] = event["evidence_id"]
                    response = http(ports["control"], "/commands", control_secret, revoke)
                else:
                    observation["controller_decision"] = "This baseline does not react to confirmed compromise."
                    observations.append(observation)
                    continue
            elif kind == "duplicate_response":
                if revoke is None:
                    observation["controller_decision"] = "No revocation command exists in this baseline."
                    observations.append(observation)
                    continue
                response = http(ports["control"], "/commands", control_secret, revoke)
            elif kind == "issue_replacement":
                replacement_command = command_payload(contract, "replace-A-v1", "A", "issue_replacement", tick, 1)
                response = http(ports["control"], "/commands", control_secret, replacement_command)
                if response["status"] != 200:
                    raise AssertionError("Replacement credential was not issued")
                credentials["A-replacement"] = response["body"]["credential"]
            elif kind == "stale_response":
                response = http(ports["control"], "/commands", control_secret,
                                command_payload(contract, "stale-A-v1", "A", "revoke_credential", tick, 1))
            elif kind == "duplicate_replacement":
                response = http(ports["control"], "/commands", control_secret, replacement_command)
                observation["same_replacement_credential"] = response["body"].get("credential") == credentials["A-replacement"]
            elif kind == "conflicting_duplicate":
                conflicting = dict(replacement_command, action="revoke_credential")
                response = http(ports["control"], "/commands", control_secret, conflicting)
            elif kind == "expired_response":
                response = http(ports["control"], "/commands", control_secret,
                                command_payload(contract, "expired-A-v2", "A", "revoke_credential", tick - 2, 2, ttl=1))
            else:
                raise AssertionError("Unknown declared event")
            observation["response"] = public_response(response)
            observations.append(observation)
        return {"mode": mode, "workload_digest": digest(workload), "contract_digest": digest(contract),
                "control_authentication_probe": public_response(control_probe),
                "phase_ticks": {"confirmation": confirmation_tick, "replacement": replacement_tick},
                "summary": summarize(observations), "observations": observations}
    finally:
        if process.stdin:
            process.stdin.close()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=5)
        for stream in (process.stdout, process.stderr):
            if stream:
                stream.close()


def verify(runs):
    by_mode = {run["mode"]: run for run in runs}
    checks = []

    def check(name, condition):
        checks.append({"name": name, "passed": bool(condition)})
        if not condition:
            raise AssertionError(name)

    def event(mode, event_id):
        return next(item for item in by_mode[mode]["observations"] if item["event"]["id"] == event_id)

    scoped = by_mode["scope_and_revocation"]["summary"]
    baseline = by_mode["no_containment"]["summary"]
    naive = by_mode["naive_volume"]["summary"]
    scope_only = by_mode["scope_only"]["summary"]
    check("identical declared workloads", len({run["workload_digest"] for run in runs}) == 1)
    check("identical access contracts", len({run["contract_digest"] for run in runs}) == 1)
    check("scope blocks cross-owner requests", scoped["scope_probes"]["record_transmissions"] == 0)
    check("ordinary scope alone blocks cross-owner requests", scope_only["scope_probes"]["record_transmissions"] == 0)
    check("scope alone cannot distinguish stolen credential within allowed scope", scope_only["credential_misuse"]["record_transmissions"] == baseline["credential_misuse"]["record_transmissions"])
    check("revocation benefit isolated from scope enforcement", scope_only["misuse_after_confirmation"]["record_transmissions"] > scoped["misuse_after_confirmation"]["record_transmissions"])
    check("same stolen credential leaks before confirmation", scoped["misuse_before_confirmation"]["record_transmissions"] == 3)
    check("revocation stops subsequent stolen-credential responses", scoped["misuse_after_confirmation"]["record_transmissions"] == 0)
    check("replacement never reactivates revoked original", scoped["original_after_replacement"]["record_transmissions"] == 0)
    check("all permitted batch requests continue", scoped["B_authorized_batch"]["http_200"] == scoped["B_authorized_batch"]["requests"])
    check("containment also denies legitimate use of affected credential", event("scope_and_revocation", "e14b")["response"]["status"] == 401)
    check("A availability cost is recorded", scoped["A_legitimate"]["http_200"] < scope_only["A_legitimate"]["http_200"])
    check("naive cutoff harms legitimate batch work", naive["B_authorized_batch"]["http_200"] < baseline["B_authorized_batch"]["http_200"])
    check("naive cutoff misses slow misuse", naive["misuse_before_confirmation"]["record_transmissions"] == 3 and naive["misuse_after_confirmation"]["record_transmissions"] > 0)
    check("issuance alone is not revocation", baseline["original_after_replacement"]["record_transmissions"] > 0)
    check("untrusted text grants no scope", event("scope_and_revocation", "e11")["response"]["status"] == 403)
    check("repeat revocation is idempotent", event("scope_and_revocation", "e14")["response"]["body"].get("duplicate") is True)
    for mode in MODES:
        check(f"{mode}: stale generation rejected", event(mode, "e21")["response"]["body"].get("error") == "stale_credential_generation")
        check(f"{mode}: duplicate replacement unchanged", event(mode, "e22").get("same_replacement_credential") is True and event(mode, "e22")["response"]["body"].get("generation") == 2)
        check(f"{mode}: conflicting duplicate rejected", event(mode, "e23")["response"]["body"].get("error") == "command_id_conflict")
        check(f"{mode}: expired response rejected", event(mode, "e24")["response"]["body"].get("error") == "command_expired_or_not_yet_valid")
    check("replacement remains usable after stale/expired commands", event("scope_and_revocation", "e25")["response"]["status"] == 200)
    return checks


def main():
    contract = json.loads((BASE / "contract.json").read_text())
    workload = json.loads((BASE / "workload.json").read_text())
    runs = [run_mode(mode, contract, workload) for mode in MODES]
    checks = verify(runs)
    report = {"experiment": "reference-defense-1", "generated_at": datetime.now(timezone.utc).isoformat(),
              "scope": "Local synthetic HTTP experiment; no LLM, sponsor integration, public deployment or government-system testing.",
              "clock": "Logical ticks; do not interpret as measured seconds or detection latency.",
              "records": "Fictional; IDs counted from actual HTTP response bodies by a separate client process.",
              "source_sha256": {name: hashlib.sha256((BASE / name).read_bytes()).hexdigest() for name in ("service.py", "run_experiment.py")},
              "runs": runs, "checks": checks}
    destination = BASE / "results.json"
    serialized = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    destination.write_text(serialized)
    summary = {"experiment": report["experiment"], "generated_at": report["generated_at"],
               "workload_digest": digest(workload), "contract_digest": digest(contract),
               "results": [{"mode": run["mode"], "metrics": run["summary"]} for run in runs],
               "checks_passed": len(checks), "checks_total": len(checks)}
    (BASE / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    for run in runs:
        metrics = run["summary"]
        print(f"{run['mode']}: misuse records={metrics['credential_misuse']['record_transmissions']}; "
              f"cross-owner records={metrics['scope_probes']['record_transmissions']}; "
              f"batch requests served={metrics['B_authorized_batch']['http_200']}/{metrics['B_authorized_batch']['requests']}")
    print(f"Passed {len(checks)} declared checks; results saved to {destination}")


if __name__ == "__main__":
    main()
