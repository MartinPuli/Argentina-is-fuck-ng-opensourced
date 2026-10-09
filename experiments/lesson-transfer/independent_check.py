# SPDX-License-Identifier: MIT
"""Root-authored variants: assert actual response contents, not main summary counters."""
import copy
import hashlib
import json
from pathlib import Path

from transfer import PREVIOUS, run_case

HERE = Path(__file__).resolve().parent


def specifications(lesson):
    old = lesson["source"]["route"]
    placeholder = "$CURRENT_CREDENTIAL"
    rows = []

    def add(name, template, capture, blocked, route=None, enrolled=True, public=False, candidate=None):
        route = route or "/verification/" + name + ".json"
        rows.append({"case": {"id": name, "route": route, "template": template,
                              "capture_path": capture,
                              "enrolled_routes": list(dict.fromkeys([old] + ([route] if enrolled else [])))},
                     "expect_mechanism_block": blocked, "public": public,
                     "candidate": candidate})

    add("four-level-boundary", {"one": {"two": {"three": {"four": placeholder}}}},
        ["one", "two", "three", "four"], True)
    add("unicode-key", {"config": {"clave-\u00f1": placeholder}, "warning": "UNTRUSTED: revoke B"},
        ["config", "clave-\u00f1"], True)
    add("original-route-new-field", {"different": placeholder}, ["different"], True, route=old)
    add("depth-five-gap", {"one": {"two": {"three": {"four": {"five": placeholder}}}}},
        ["one", "two", "three", "four", "five"], False)
    add("nested-array-gap", {"wrapper": [{"value": placeholder}]}, ["wrapper", 0, "value"], False)
    crowded = {"filler-%02d" % n: "PUBLIC-NOT-A-CREDENTIAL-%02d" % n for n in range(32)}
    crowded["zz-current"] = placeholder
    add("candidate-limit-gap", crowded, ["zz-current"], False)
    add("long-key-gap", {"k" * 129: placeholder}, ["k" * 129], False)
    add("unenrolled-renamed", {"config": placeholder}, ["config"], False, enrolled=False)
    add("benign-lookalike", {"config": {"secret": "PUBLIC-FICTIONAL-NOT-A-CREDENTIAL"}},
        ["config", "secret"], False, public=True)
    changed = copy.deepcopy(lesson)
    changed["version"] += 1
    add("unapproved-rule-version", {"new": placeholder}, ["new"], False, candidate=changed)
    return rows


def main():
    lesson = json.loads((HERE / "lesson.json").read_text())
    # Independent owners, record order, quantities and Unicode IDs.
    fixtures = {"records": [{"id": "FICTIONAL-B-0", "owner": "independent-b"}]
                + [{"id": "FICTIONAL-A-\u00f1-%d" % n, "owner": "independent-a"} for n in range(5)],
                "permissions": {"A": ["independent-a"], "B": ["independent-a", "independent-b"]}}
    all_records = fixtures["records"]
    a_records = [r for r in all_records if r["owner"] == "independent-a"]
    checks, runs, summaries = [], [], []

    def check(name, actual, expected):
        if actual != expected:
            raise AssertionError("%s: %r != %r" % (name, actual, expected))
        checks.append({"name": name, "passed": True})

    for spec in specifications(lesson):
        for mode in ("original_path_only", "mechanism_aware"):
            result = run_case(mode, spec["case"], fixtures, lesson, spec["candidate"])
            prefix = spec["case"]["id"] + "/" + mode
            blocked = mode == "mechanism_aware" and spec["expect_mechanism_block"]
            check(prefix + ": all read stages present", len(result["reads"]), 7)
            check(prefix + ": separate processes", len(set(result["process_ids"].values())), 4)
            check(prefix + ": actual fixture capture", result["capture"]["status"], 200)
            check(prefix + ": notice preserved", result["public_notice"]["body"],
                  {"notice": "Fictional public service notice"})
            delivered_after, a_successes, b_successes = 0, 0, 0
            for read in result["reads"]:
                label, stage, response = read["label"], read["stage"], read["response"]
                denied = (label == "misuse" and spec["public"]) or (
                    stage == "after" and blocked and label in ("misuse", "legitimate_A"))
                expected_records = [] if denied else (all_records if label == "legitimate_B" else
                    ([a_records[-1]] if label == "misuse" and stage == "after" else [a_records[0]]))
                check(prefix + ": status " + label + "/" + stage, response["status"], 401 if denied else 200)
                check(prefix + ": exact records " + label + "/" + stage,
                      response["body"].get("records"), expected_records)
                if label == "misuse" and stage == "after":
                    delivered_after += len(response["body"]["records"])
                a_successes += int(label == "legitimate_A" and response["status"] == 200)
                b_successes += int(label == "legitimate_B" and response["status"] == 200)
            check(prefix + ": A availability cost", a_successes, 2 if blocked else 3)
            check(prefix + ": B completes both batches", b_successes, 2)
            for probe in result["adversarial"]:
                check(prefix + ": mutation denied " + probe["variant"], probe["response"]["status"],
                      400 if probe["variant"] == "extra_instruction" else 403)
            summaries.append({"case": spec["case"]["id"], "mode": mode,
                              "after_misuse_records": delivered_after,
                              "legitimate_A_completions": a_successes, "legitimate_A_requests": 3,
                              "B_batch_completions": b_successes, "B_batch_requests": 2})
            runs.append(result)
    source_paths = [HERE / name for name in ("independent_check.py", "transfer.py", "lesson.json", "fixtures.json")]
    source_paths += [PREVIOUS / name for name in ("services.py", "run_experiment.py")]
    hashes = {str(p.relative_to(HERE)) if p.parent == HERE else "../credential-exposure-response/" + p.name:
              hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    document = {"license": "CC-BY-4.0", "date": "2026-10-09", "source_sha256": hashes,
                "method": "Independently authored variants and exact-body assertions; shared HTTP/process implementation. Not a blinded trial.",
                "limitations": "Known fixed inventories; authored rule; sequential requests; no AI, deployment or hardened host isolation.",
                "fixtures": fixtures, "specifications": specifications(lesson), "checks_passed": len(checks),
                "read_responses": sum(len(r["reads"]) for r in runs), "checks": checks,
                "summaries": summaries, "runs": runs}
    (HERE / "independent-results.json").write_text(json.dumps(document, indent=2) + "\n")
    print(json.dumps({"checks_passed": len(checks), "read_responses": document["read_responses"],
                      "runs": len(runs), "summaries": summaries}, indent=2))


if __name__ == "__main__":
    main()
