# SPDX-License-Identifier: MIT
"""Independent scenario variants; use HTTP observations, not the fixture's verify().

Written after the initial implementation. These are additional regression cases,
not a blinded evaluation of an AI model or a production benchmark.
"""
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from run_experiment import run_mode

BASE = Path(__file__).resolve().parent


def scenario(name, original_contract, original_workload):
    contract = copy.deepcopy(original_contract)
    workload = copy.deepcopy(original_workload)
    if name == "renamed_records_shifted_clock":
        names = dict(zip(contract["owners"], ["district_north", "district_south", "district_west"]))
        contract["owners"] = [names[owner] for owner in contract["owners"]]
        contract["records_per_owner"] = 13
        for policy in contract["identities"].values():
            policy["owners"] = [names[owner] for owner in policy["owners"]]
        for event in workload["events"]:
            event["tick"] = 7 + 3 * event["tick"]
            if event.get("owner") in names:
                event["owner"] = names[event["owner"]]
            if "record_ids" in event:
                event["record_ids"] = [names[value.rsplit("-", 1)[0]] + "-" + value.rsplit("-", 1)[1]
                                       for value in event["record_ids"]]
    elif name == "larger_requests_and_additional_scope_probe":
        for event in workload["events"]:
            if event.get("intent") == "credential_misuse":
                event["record_ids"] = ["alice-02", "alice-04", "alice-08"]
        workload["events"].append({
            "id": "variant-batch-escalation", "tick": 19.5, "kind": "read",
            "credential": "A-original", "owner": "all", "intent": "unauthorized_scope_probe",
        })
        workload["events"].sort(key=lambda event: event["tick"])
    elif name == "slower_pace_and_reordered_initial_requests":
        for event in workload["events"]:
            event["tick"] *= 20
        # Both original first requests occur at tick zero; change their order.
        workload["events"][0], workload["events"][1] = workload["events"][1], workload["events"][0]
    else:
        raise ValueError(name)
    return contract, workload


def verify_observations(run, contract, workload):
    # Deliberately do not use run['summary'] or run_experiment.verify().
    by_event = {item["event"]["id"]: item for item in run["observations"]}
    confirmation = next(event["tick"] for event in workload["events"] if event["kind"] == "confirmed_compromise")
    replacement = next(event["tick"] for event in workload["events"] if event["kind"] == "issue_replacement")
    result = {"mode": run["mode"], "requests_checked": 0, "misuse_records_before_confirmation": 0,
              "misuse_records_after_confirmation": 0, "scope_violation_records": 0,
              "legitimate_A_denied": 0, "legitimate_B_succeeded": 0, "legitimate_B_total": 0}
    for event in workload["events"]:
        if event["kind"] != "read":
            continue
        observed = by_event[event["id"]]["response"]
        body = observed["body"]
        received = [row["id"] for row in body.get("records", [])]
        identity = event["credential"].split("-", 1)[0]
        is_scope_violation = event["intent"] == "unauthorized_scope_probe"
        is_revoked = (run["mode"] == "scope_and_revocation"
                      and event["credential"] == "A-original" and event["tick"] > confirmation)
        expect_denied = is_scope_violation or is_revoked
        if expect_denied:
            assert observed["status"] in (401, 403), (event["id"], observed)
            assert not received, (event["id"], "denied response exposed records")
        else:
            assert observed["status"] == 200, (event["id"], observed)
            expected = {f"{owner}-{number:02}" for owner in contract["owners"]
                        if event["owner"] == "all" or owner == event["owner"]
                        for number in range(1, contract["records_per_owner"] + 1)}
            if "record_ids" in event:
                expected &= set(event["record_ids"])
            assert set(received) == expected and len(received) == len(expected), (event["id"], received, expected)
        if event["intent"] == "credential_misuse":
            bucket = "misuse_records_before_confirmation" if event["tick"] < confirmation else "misuse_records_after_confirmation"
            result[bucket] += len(received)
        if is_scope_violation:
            result["scope_violation_records"] += len(received)
        if identity == "A" and event["intent"] == "legitimate" and observed["status"] != 200:
            result["legitimate_A_denied"] += 1
        if identity == "B" and event["intent"] == "legitimate":
            result["legitimate_B_total"] += 1
            result["legitimate_B_succeeded"] += observed["status"] == 200
        if run["mode"] == "scope_and_revocation" and event["credential"] == "A-original" and event["tick"] > replacement:
            assert observed["status"] == 401
        result["requests_checked"] += 1
    assert result["misuse_records_before_confirmation"] > 0, "Must expose pre-confirmation limitation"
    assert result["legitimate_B_succeeded"] == result["legitimate_B_total"] > 0
    assert result["scope_violation_records"] == 0
    if run["mode"] == "scope_and_revocation":
        assert result["misuse_records_after_confirmation"] == 0
        assert result["legitimate_A_denied"] > 0, "Must expose affected-service availability cost"
    else:
        assert result["misuse_records_after_confirmation"] > 0
        assert result["legitimate_A_denied"] == 0
    return result


def main():
    contract = json.loads((BASE / "contract.json").read_text())
    workload = json.loads((BASE / "workload.json").read_text())
    results = []
    for name in ("renamed_records_shifted_clock", "larger_requests_and_additional_scope_probe",
                 "slower_pace_and_reordered_initial_requests"):
        variant_contract, variant_workload = scenario(name, contract, workload)
        for mode in ("scope_only", "scope_and_revocation"):
            run = run_mode(mode, variant_contract, variant_workload)
            measured = verify_observations(run, variant_contract, variant_workload)
            results.append({"scenario": name, **measured, "observations": run["observations"]})
    report = {"generated_at": datetime.now(timezone.utc).isoformat(),
              "description": "Three independently specified regression variants, two modes, actual local HTTP bodies.",
              "limitations": "Same implementation and trusted evidence event; no AI, external deployment, production isolation or statistical generalization.",
              "source_sha256": {name: hashlib.sha256((BASE / name).read_bytes()).hexdigest()
                                for name in ("service.py", "run_experiment.py", "independent_variants.py")},
              "runs": results, "all_checks_passed": True}
    (BASE / "independent-results.json").write_text(json.dumps(report, indent=2) + "\n")
    for result in results:
        print(f"{result['scenario']} / {result['mode']}: checked {result['requests_checked']} HTTP reads; "
              f"post-confirmation misuse records={result['misuse_records_after_confirmation']}; "
              f"A legitimate denied={result['legitimate_A_denied']}; "
              f"B served={result['legitimate_B_succeeded']}/{result['legitimate_B_total']}")


if __name__ == "__main__":
    main()
