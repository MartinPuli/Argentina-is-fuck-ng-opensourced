# SPDX-License-Identifier: MIT
"""Reproduce the publication experiment with fresh local staging and separate HTTP clients."""
import copy
import json
import select
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from publisher import (ReleaseRejected, digest, incremental_build, inventory,
                       prepare_sources, release_gate, sha256, unsafe_publish)

HERE = Path(__file__).resolve().parent


def probe_http(deploy_root, fixture, release_manifest=None):
    """The publisher does not supply success counters; a separate process reads HTTP bytes."""
    config = {"host": "127.0.0.1", "deploy_root": str(deploy_root)}
    process = subprocess.Popen([sys.executable, str(HERE / "serve_local.py")],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
    try:
        process.stdin.write(json.dumps(config) + "\n")
        process.stdin.flush()
        readable, _, _ = select.select([process.stdout], [], [], 10)
        if not readable:
            raise RuntimeError("Local HTTP server did not report readiness")
        line = process.stdout.readline()
        if not line:
            raise RuntimeError("Local HTTP server failed: " + process.stderr.read())
        port = json.loads(line)["port"]
        verifier_config = dict(config, port=port, fixture=fixture, release_manifest=release_manifest)
        result = subprocess.run([sys.executable, str(HERE / "verify_http.py")],
                                input=json.dumps(verifier_config), text=True,
                                capture_output=True, timeout=30, check=True)
        return json.loads(result.stdout)
    finally:
        if process.stdin:
            process.stdin.close()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=5)
        process.stdout.close()
        process.stderr.close()


def rejected(operation, deploy_root):
    try:
        operation()
    except ReleaseRejected as error:
        return {"released": False, "reason": error.reason, "evidence": error.evidence,
                "deployment_directory_created": Path(deploy_root).exists()}
    raise AssertionError("Negative release case was unexpectedly accepted")


def run_case(fixture, policy):
    """Generic importable runner: returns observations, writes no persistent result files.

    Alter fixture IDs, content and paths for additional variants. All staging is newly
    allocated; the supplied fixture and policy are copied and are not mutated.
    """
    fixture, policy = copy.deepcopy(fixture), copy.deepcopy(policy)
    if fixture.get("fictional_data") is not True:
        raise ValueError("This local runner accepts declared fictional fixtures only")
    private = [item for item in fixture["sources"] if item.get("classification") == "private"]
    public = [item for item in fixture["sources"] if item.get("classification") == "public"]
    if not private or not public:
        raise ValueError("Comparison requires public and private fixture sources")
    declared_paths = sorted({path for item in fixture["sources"] for path in item["artifact_paths"]}
                            | set(fixture.get("probe_paths", [])))
    protocol = {"host": "127.0.0.1", "method": "GET", "authentication": "none",
                "declared_paths": declared_paths,
                "discovery": "also probe each regular file independently found in deployed output",
                "content_check": "compare bytes and search every response for each private payload or marker"}
    result = {"case_id": fixture["case_id"], "fixture_sha256": digest(fixture),
              "policy_sha256": digest(policy), "probe_protocol": protocol,
              "probe_protocol_sha256": digest(protocol), "conditions": {}}
    with tempfile.TemporaryDirectory(prefix="synthetic-publication-") as directory:
        root = Path(directory)
        source = root / "original-source"
        source_manifest = prepare_sources(fixture, source)
        base_build = root / "baseline-build"
        base_manifest = incremental_build(source, source_manifest, base_build)
        base_deploy = root / "baseline-deploy"
        unsafe_publish(base_build, base_deploy)
        result["conditions"]["baseline"] = {
            "source_manifest": source_manifest, "build_manifest": base_manifest,
            "actual_build_inventory": inventory(base_build),
            "http": probe_http(base_deploy, fixture)}

        # The source-level fix is real: private files and their entries disappear.
        # Reusing a cached build without deletion still leaves previous copies on disk.
        fixed_fixture = copy.deepcopy(fixture)
        fixed_fixture["sources"] = public
        fixed_source = root / "fixed-source"
        fixed_source_manifest = prepare_sources(fixed_fixture, fixed_source)
        fixed_build = root / "incremental-fixed-build"
        shutil.copytree(base_build, fixed_build)
        fixed_manifest = incremental_build(fixed_source, fixed_source_manifest, fixed_build)
        fixed_deploy = root / "source-only-fixed-deploy"
        unsafe_publish(fixed_build, fixed_deploy)
        private_source_paths = [item["source_path"] for item in private]
        result["conditions"]["source_only_fix"] = {
            "source_manifest": fixed_source_manifest, "build_manifest": fixed_manifest,
            "actual_source_inventory": inventory(fixed_source),
            "private_sources_physically_absent": all(not (fixed_source / path).exists()
                                                     for path in private_source_paths),
            "actual_build_inventory": inventory(fixed_build),
            "http": probe_http(fixed_deploy, fixture)}

        dirty_deploy = root / "dirty-gated-deploy"
        result["dirty_build_gate"] = rejected(
            lambda: release_gate(fixed_build, fixed_manifest, fixed_source_manifest, policy, dirty_deploy),
            dirty_deploy)

        # Start a fresh build; retain the complete classified source manifest.
        clean_build = root / "fresh-public-build"
        clean_manifest = incremental_build(source, source_manifest, clean_build, public_only=True, policy=policy)
        final_deploy = root / "fresh-approved-deploy"
        final_manifest = release_gate(clean_build, clean_manifest, source_manifest, policy, final_deploy)
        result["conditions"]["approved_release_gate"] = {
            "source_manifest": source_manifest, "build_manifest": clean_manifest,
            "actual_build_inventory": inventory(clean_build), "release_manifest": final_manifest,
            "http": probe_http(final_deploy, fixture, final_manifest)}

        # An absent classification blocks the release pipeline; it is not counted as
        # a denied HTTP request, because no deployment/server is created for this case.
        missing_fixture = copy.deepcopy(fixture)
        missing_fixture["sources"][0].pop("classification", None)
        missing_manifest = prepare_sources(missing_fixture, root / "unclassified-source")
        missing_deploy = root / "unclassified-deploy"
        result["missing_classification_gate"] = rejected(
            lambda: release_gate(clean_build, clean_manifest, missing_manifest, policy, missing_deploy),
            missing_deploy)

        # Check byte integrity separately from naming or the manifest's assertion.
        tampered_build = root / "tampered-build"
        shutil.copytree(clean_build, tampered_build)
        tampered_path = clean_manifest[0]["path"]
        (tampered_build / tampered_path).write_bytes(private[0]["content"].encode())
        tampered_deploy = root / "tampered-deploy"
        result["changed_content_gate"] = rejected(
            lambda: release_gate(tampered_build, clean_manifest, source_manifest, policy, tampered_deploy),
            tampered_deploy)

        # Expose a deliberate limitation: byte integrity cannot correct a false
        # owner classification. The independent oracle still knows the private bytes.
        mislabeled_fixture = copy.deepcopy(fixture)
        mislabeled_public = next(item for item in mislabeled_fixture["sources"]
                                 if item["classification"] == "public")
        mislabeled_public["content"] += private[0]["content"]
        mislabeled_source = root / "misclassified-source"
        mislabeled_manifest = prepare_sources(mislabeled_fixture, mislabeled_source)
        mislabeled_build = root / "misclassified-build"
        mislabeled_built = incremental_build(mislabeled_source, mislabeled_manifest,
                                            mislabeled_build, public_only=True, policy=policy)
        mislabeled_deploy = root / "misclassified-deploy"
        mislabeled_release = release_gate(mislabeled_build, mislabeled_built,
                                          mislabeled_manifest, policy, mislabeled_deploy)
        result["misclassification_counterexample"] = {
            "approved_public_source_contains_private_fixture_content": mislabeled_public["id"],
            "fixture_sha256": digest(mislabeled_fixture), "released": True,
            "release_manifest": mislabeled_release,
            "http": probe_http(mislabeled_deploy, mislabeled_fixture, mislabeled_release)}

        baseline_http = result["conditions"]["baseline"]["http"]
        result["previously_fetched_private_response_bodies_retained_in_results"] = sum(
            bool(item["private_matches"]) and bool(item["body_base64"])
            for item in baseline_http["observations"])
    return result


def check_case(case, fixture):
    """Meaningful contract assertions; metrics remain independent client observations."""
    checks = []

    def require(name, condition):
        checks.append({"name": name, "passed": bool(condition)})
        if not condition:
            raise AssertionError(f"{case['case_id']}: {name}")

    private_paths = {path for item in fixture["sources"] if item["classification"] == "private"
                     for path in item["artifact_paths"]}
    public_paths = {path for item in fixture["sources"] if item["classification"] == "public"
                   for path in item["artifact_paths"]}
    expected_private_ids = sorted(item["id"] for item in fixture["sources"] if item["classification"] == "private")
    conditions = case["conditions"]
    for name in ("baseline", "source_only_fix"):
        http = conditions[name]["http"]
        metrics = http["metrics"]
        require(name + "_all_private_aliases_deliver_exact_content",
                metrics["private_exact_content_responses"] == len(private_paths))
        require(name + "_private_source_ids_confirmed", metrics["private_source_ids_exposed"] == expected_private_ids)
        require(name + "_all_public_content_continues", metrics["public_exact_successes"] == len(public_paths))
    fixed = conditions["source_only_fix"]
    require("source_fix_physically_removed_private_sources", fixed["private_sources_physically_absent"])
    require("source_fix_current_manifest_contains_only_public_entries",
            all(item["classification"] == "public" for item in fixed["source_manifest"]))
    require("source_fix_left_stale_private_artifacts", private_paths <= set(fixed["actual_build_inventory"]))
    require("dirty_build_rejected_for_unmanifested_files",
            case["dirty_build_gate"]["reason"] == "build_manifest_set_mismatch"
            and not case["dirty_build_gate"]["deployment_directory_created"])
    require("dirty_gate_found_exact_stale_paths",
            set(case["dirty_build_gate"]["evidence"]["unmanifested"]) == private_paths)
    final = conditions["approved_release_gate"]["http"]
    require("final_no_private_payload_or_marker_in_any_response", final["metrics"]["private_exposing_responses"] == 0)
    require("final_all_public_content_continues", final["metrics"]["public_exact_successes"] == len(public_paths))
    require("final_private_paths_are_http_404", all(item["status"] == 404 for item in final["observations"] if item["path"] in private_paths))
    require("release_manifest_equals_independent_physical_inventory", final["release_manifest_exact_artifact_set"] is True)
    require("release_manifest_equals_observed_http_200_set_and_hashes", final["release_manifest_exact_http_set"] is True)
    require("same_probe_paths_in_all_three_conditions", len({tuple(item["path"] for item in value["http"]["observations"])
                                                           for value in conditions.values()}) == 1)
    require("missing_classification_blocks_without_deployment", case["missing_classification_gate"]["reason"] == "unclassified_source"
            and not case["missing_classification_gate"]["deployment_directory_created"])
    require("changed_public_artifact_bytes_rejected", case["changed_content_gate"]["reason"] == "artifact_hash_mismatch"
            and not case["changed_content_gate"]["deployment_directory_created"])
    require("previously_fetched_private_copies_not_retracted", case["previously_fetched_private_response_bodies_retained_in_results"] == len(private_paths))
    counterexample = case["misclassification_counterexample"]
    require("misclassified_public_content_really_exposes_private_bytes",
            counterexample["released"] and counterexample["http"]["metrics"]["private_exposing_responses"] > 0)
    require("manifest_integrity_alone_does_not_prove_confidentiality",
            counterexample["http"]["release_manifest_exact_artifact_set"] is True
            and counterexample["http"]["release_manifest_exact_http_set"] is True)
    return checks


def main():
    policy = json.loads((HERE / "lesson-policy.json").read_text())
    fixtures = [json.loads((HERE / name).read_text()) for name in ("fixture.json", "heldout-fixture.json")]
    cases = [run_case(fixture, policy) for fixture in fixtures]
    checks = {case["case_id"]: check_case(case, fixture) for case, fixture in zip(cases, fixtures)}
    same_policy = len({case["policy_sha256"] for case in cases}) == 1
    if not same_policy:
        raise AssertionError("Policy changed across cases")
    names = ["publisher.py", "serve_local.py", "verify_http.py", "run_experiment.py",
             "fixture.json", "heldout-fixture.json", "lesson-policy.json"]
    output = {"experiment": "local-synthetic-publication-regression", "schema_version": 1,
              "license": "CC-BY-4.0", "network_scope": "127.0.0.1 only",
              "code_and_fixture_file_sha256": {name: sha256((HERE / name).read_bytes()) for name in names},
              "policy": policy, "same_policy_across_cases": same_policy, "cases": cases, "checks": checks}
    summary = {"experiment": output["experiment"], "license": "CC-BY-4.0",
               "results_sha256": digest(output), "checks_passed": sum(len(value) for value in checks.values()) + 1,
               "same_policy_across_cases": same_policy, "cases": []}
    for case in cases:
        summary["cases"].append({"case_id": case["case_id"], "fixture_sha256": case["fixture_sha256"],
                                 "policy_sha256": case["policy_sha256"],
                                 "conditions": {name: value["http"]["metrics"] for name, value in case["conditions"].items()},
                                 "gate_rejections": {name: case[name]["reason"] for name in
                                                     ("dirty_build_gate", "missing_classification_gate", "changed_content_gate")},
                                 "misclassification_counterexample": case["misclassification_counterexample"]["http"]["metrics"]})
    (HERE / "results.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
