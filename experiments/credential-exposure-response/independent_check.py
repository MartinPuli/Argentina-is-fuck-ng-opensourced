# SPDX-License-Identifier: MIT
"""Root-authored changed workloads; uses service startup, not main-case verifier."""
import hashlib
import json
from pathlib import Path

from run_experiment import run_mode

HERE = Path(__file__).resolve().parent


def variant(size, route, prefix):
    a = [f"{prefix}-private-{i}" for i in range(size)]
    b = [f"{prefix}-other-{i}" for i in range(3)]
    protocol = {
        "bind": "127.0.0.1", "enrolled_identity": "A", "exposure_route": route,
        "permissions": {"A": ["department-one"], "B": ["department-one", "department-two"]},
        "records": ([{"id": x, "owner": "department-two"} for x in reversed(b)] +
                    [{"id": x, "owner": "department-one"} for x in reversed(a)]),
    }
    events = []

    def read(name, ids, credential="stolen_initial", app=False, label="misuse"):
        events.append({"id": name, "op": "read", "ids": ids,
                       "via": "app" if app else "gateway", "credential": credential, "label": label})

    events.append({"id": "initial_capture", "op": "capture", "slot": "stolen_initial"})
    read("mixed_scope", [a[0], b[0]], label="cross_owner")
    read("unknown_record", [prefix + "-absent"], label="invalid")
    read("misuse_before", a[:2])
    read("A_before", a[:1], app=True, label="legitimate_A")
    read("B_before", a + b, credential="B", label="legitimate_B")
    for kind in ("wrong_origin", "false_digest", "wrong_target", "unauthenticated"):
        events.append({"id": kind, "op": "claim", "variant": kind})
    read("A_after_false_claims", a[-1:], app=True, label="legitimate_A")
    events.append({"id": "observed_first", "op": "observe"})
    read("old_after_response", a[:3])
    read("A_after_response", a[-1:], app=True, label="legitimate_A")
    read("B_during_response", b + a, credential="B", label="legitimate_B")
    events.append({"id": "recover_once", "op": "recover", "expected_generation": 1})
    read("old_after_replacement", a[-2:])
    events.append({"id": "replacement_capture", "op": "capture", "slot": "stolen_second"})
    read("replacement_misuse", a[:2], credential="stolen_second")
    read("A_recovered", a[:1], app=True, label="legitimate_A")
    events.append({"id": "observed_again", "op": "observe"})
    events.append({"id": "old_evidence_new_id", "op": "replay", "variant": "stale"})
    events.append({"id": "old_evidence_same_id", "op": "replay", "variant": "same"})
    read("A_final", a[-1:], app=True, label="legitimate_A")
    read("B_final", a + b, credential="B", label="legitimate_B")
    read("old_final", a[-1:])
    return protocol, {"events": events}


def main():
    checks, outputs = [], []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append({"name": name, "passed": True})

    for case, args in enumerate(((5, "/renamed/config.json", "fictional"),
                                 (17, "/v7/diagnostics/export", "ficción-測試"))):
        protocol, workload = variant(*args)
        for mode in ("scope_only", "repair_only", "revoke_only", "combined"):
            result = run_mode(mode, protocol, workload)
            events = {e["id"]: e for e in result["transcript"]}
            tag = f"case{case}:{mode}:"
            revoked = mode in ("revoke_only", "combined")
            repaired = mode in ("repair_only", "combined")
            read_count = 0
            transmissions = 0
            for expected in workload["events"]:
                if expected["op"] != "read":
                    continue
                name = expected["id"]
                response = events[name]["response"]
                status = 200
                if name == "mixed_scope":
                    status = 403
                elif name == "unknown_record":
                    status = 404
                elif name in ("old_after_response", "old_after_replacement", "old_final", "A_after_response") and revoked:
                    status = 401
                elif name == "replacement_misuse" and repaired:
                    status = 401
                elif name == "A_final" and mode == "revoke_only":
                    status = 401
                ids = [r["id"] for r in response["body"].get("records", [])]
                check(tag + name + ":status", response["status"] == status)
                check(tag + name + ":actual_ids", ids == (expected["ids"] if status == 200 else []))
                read_count += 1
                transmissions += len(ids)
            for name, status in (("wrong_origin", 403), ("false_digest", 422),
                                 ("wrong_target", 403), ("unauthenticated", 401),
                                 ("old_evidence_new_id", 409)):
                check(tag + name, events[name]["response"]["status"] == status)
            check(tag + "duplicate does not reapply action",
                  events["old_evidence_same_id"]["response"]["body"].get("duplicate") is True)
            check(tag + "actual observation exists",
                  events["observed_first"]["observation"]["observation"]["status"] == 200)
            check(tag + "replacement exposure measured",
                  events["replacement_capture"]["response"]["status"] == (404 if repaired else 200))
            outputs.append({"case": case, "mode": mode, "read_responses_checked": read_count,
                            "record_transmissions": transmissions, "protocol": protocol,
                            "workload": workload, "run": result})
    sources = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
               for name in ("services.py", "run_experiment.py", "independent_check.py")}
    report = {
        "scope": "Eight sequential local runs with changed routes, owners, record counts and identifiers; not blinded or representative.",
        "limitations": "Shared service implementation and same OS user; no LLM, sponsor call, concurrency, production isolation or timing inference.",
        "source_sha256": sources, "assertions_passed": len(checks),
        "read_responses_checked": sum(r["read_responses_checked"] for r in outputs),
        "checks": checks, "runs": outputs,
    }
    (HERE / "independent-results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"runs": len(outputs), "assertions_passed": len(checks),
                      "read_responses_checked": report["read_responses_checked"]}))


if __name__ == "__main__":
    main()
