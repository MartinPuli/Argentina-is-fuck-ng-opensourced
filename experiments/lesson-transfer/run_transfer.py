# SPDX-License-Identifier: MIT
"""Main declared comparison; independent_check.py is reserved for separate review."""
import hashlib
import json
from pathlib import Path

from transfer import PREVIOUS, lesson_digest, run_case

HERE = Path(__file__).resolve().parent


def summarize(result):
    groups = {}
    for observation in result["reads"]:
        label = observation["label"]
        group = groups.setdefault(label, {"requests": 0, "completed": 0, "record_transmissions": 0,
                                          "after_records": 0, "distinct_ids": set()})
        ids = [r["id"] for r in observation["response"]["body"].get("records", [])]
        group["requests"] += 1
        group["completed"] += int(observation["response"]["status"] == 200)
        group["record_transmissions"] += len(ids)
        group["distinct_ids"].update(ids)
        if observation["stage"] == "after":
            group["after_records"] += len(ids)
    for group in groups.values():
        group["distinct_ids"] = sorted(group["distinct_ids"])
    return groups


def verify(source, results):
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append({"name": name, "passed": True})

    check("source actual HTTP credential capture", source["capture"]["status"] == 200)
    source_reads = {(r["label"], r["stage"]): r["response"] for r in source["reads"]}
    check("source actual credential works before response", source_reads["misuse", "before"]["status"] == 200)
    check("original check works on source", source_reads["misuse", "after"]["status"] == 401)
    for result in [source] + results:
        prefix = result["case"] + "/" + result["mode"]
        reads = {(r["label"], r["stage"]): r["response"] for r in result["reads"]}
        blocked = result["case"] == "source-service" or (result["case"] == "renamed-nested" and result["mode"] == "mechanism_aware")
        public = result["case"] == "public-metadata"
        check(prefix + ": separate process IDs", len(set(result["process_ids"].values())) == 4)
        check(prefix + ": misuse before", reads["misuse", "before"]["status"] == (401 if public else 200))
        check(prefix + ": actual after response", reads["misuse", "after"]["status"] == (401 if blocked or public else 200))
        check(prefix + ": A remains active after invalid evidence", reads["legitimate_A", "after_adversarial"]["status"] == 200)
        check(prefix + ": A availability cost", reads["legitimate_A", "after"]["status"] == (401 if blocked else 200))
        check(prefix + ": B before", reads["legitimate_B", "before"]["status"] == 200)
        check(prefix + ": B after", reads["legitimate_B", "after"]["status"] == 200)
        check(prefix + ": public notice", result["public_notice"]["status"] == 200)
        for probe in result["adversarial"]:
            expected = 400 if probe["variant"] == "extra_instruction" else 403
            check(prefix + ": reject " + probe["variant"], probe["response"]["status"] == expected)
    return checks


def main():
    fixtures = json.loads((HERE / "fixtures.json").read_text())
    lesson = json.loads((HERE / "lesson.json").read_text())
    source = run_case("original_path_only", fixtures["source"], fixtures, lesson)
    results = [run_case(mode, case, fixtures, lesson) for case in fixtures["cases"] for mode in fixtures["modes"]]
    checks = verify(source, results)
    for result in [source] + results:
        result["metrics"] = summarize(result)
    hashes = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
              for name in ("transfer.py", "run_transfer.py", "lesson.json", "fixtures.json", "PLAN.md")}
    for name in ("services.py", "run_experiment.py"):
        hashes["../credential-exposure-response/" + name] = hashlib.sha256((PREVIOUS / name).read_bytes()).hexdigest()
    document = {"license": "CC-BY-4.0", "source_sha256": hashes, "approved_lesson_sha256": lesson_digest(lesson),
                "lesson": lesson, "fixtures": fixtures, "source_observation": source,
                "results": results, "checks": checks}
    summary = {"license": "CC-BY-4.0", "source_sha256": hashes, "checks_passed": len(checks),
               "source_metrics": source["metrics"],
               "results": [{"case": r["case"], "mode": r["mode"], "metrics": r["metrics"]} for r in results]}
    for name, value in (("results.json", document), ("summary.json", summary)):
        (HERE / name).write_text(json.dumps(value, indent=2) + "\n")
    print(json.dumps({"checks_passed": len(checks), "case_mode_runs": len(results),
                      "outcomes": [{"case": r["case"], "mode": r["mode"],
                                    "after_misuse_records": r["metrics"]["misuse"]["after_records"],
                                    "A_completions": r["metrics"]["legitimate_A"]["completed"]} for r in results]}, indent=2))


if __name__ == "__main__":
    main()
