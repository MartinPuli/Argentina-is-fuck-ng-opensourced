# SPDX-License-Identifier: MIT
"""Local deterministic publication fixture and explicit release-policy implementation."""
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath


class ReleaseRejected(ValueError):
    def __init__(self, reason, **evidence):
        super().__init__(reason)
        self.reason = reason
        self.evidence = evidence


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ReleaseRejected("invalid_artifact_path", path=relative)
    parts = relative.split("/")
    if any(part in ("", ".", "..") for part in parts) or PurePosixPath(relative).is_absolute():
        raise ReleaseRejected("invalid_artifact_path", path=relative)
    return Path(root).joinpath(*parts)


def inventory(root):
    output = {}
    root = Path(root)
    if not root.exists():
        return output
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            if path.is_symlink():
                raise ReleaseRejected("symlink_not_supported", path=path.relative_to(root).as_posix())
        for name in files:
            path = Path(directory) / name
            if not path.is_file():
                raise ReleaseRejected("nonregular_artifact", path=path.relative_to(root).as_posix())
            output[path.relative_to(root).as_posix()] = sha256(path.read_bytes())
    return dict(sorted(output.items()))


def prepare_sources(fixture, source_root):
    source_root = Path(source_root)
    source_root.mkdir(parents=True, exist_ok=False)
    manifest = []
    ids, sources, artifacts = set(), set(), set()
    for entry in fixture["sources"]:
        source_id = entry["id"]
        source_path = entry["source_path"]
        content = entry["content"].encode("utf-8")
        if source_id in ids or source_path in sources or not content:
            raise ReleaseRejected("invalid_source_manifest", source_id=source_id)
        ids.add(source_id)
        sources.add(source_path)
        destination = safe_path(source_root, source_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        paths = entry["artifact_paths"]
        if not paths:
            raise ReleaseRejected("missing_artifact_mapping", source_id=source_id)
        for path in paths:
            safe_path(source_root, path)
            if path in artifacts:
                raise ReleaseRejected("duplicate_artifact_path", path=path)
            artifacts.add(path)
        manifest.append({"id": source_id, "source_path": source_path, "sha256": sha256(content),
                         "classification": entry.get("classification"), "artifact_paths": paths})
    return manifest


def validate_approved_sources(manifest, policy):
    if policy.get("approval_status") != "approved_for_local_synthetic_experiment":
        raise ReleaseRejected("policy_not_approved")
    if (policy.get("publishable_classifications") != ["public"]
            or policy.get("unclassified_behavior") != "reject_release"
            or policy.get("unmanifested_artifact_behavior") != "reject_release"
            or policy.get("content_integrity_behavior") != "bind_artifact_to_approved_source_hash"
            or policy.get("fresh_deployment_required") is not True):
        raise ReleaseRejected("unsupported_policy")
    for entry in manifest:
        classification = entry.get("classification")
        if classification not in policy["known_classifications"]:
            raise ReleaseRejected("unclassified_source", source_id=entry["id"])


def incremental_build(source_root, source_manifest, build_root, public_only=False, policy=None):
    """Copies current sources but intentionally never removes stale build artifacts."""
    build_root = Path(build_root)
    build_root.mkdir(parents=True, exist_ok=True)
    if public_only:
        validate_approved_sources(source_manifest, policy)
    built_manifest = []
    for entry in source_manifest:
        if public_only and entry["classification"] != "public":
            continue
        content = safe_path(source_root, entry["source_path"]).read_bytes()
        if sha256(content) != entry["sha256"]:
            raise ReleaseRejected("source_changed_after_approval", source_id=entry["id"])
        for artifact_path in entry["artifact_paths"]:
            target = safe_path(build_root, artifact_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            built_manifest.append({"path": artifact_path, "source_id": entry["id"],
                                   "classification": entry["classification"], "sha256": sha256(content)})
    return built_manifest


def unsafe_publish(build_root, deploy_root):
    """Credible unsafe baseline: copy the entire cached build tree, not only current sources."""
    shutil.copytree(build_root, deploy_root)


def release_gate(build_root, built_manifest, source_manifest, policy, deploy_root):
    """Only known, explicitly public, hash-bound artifacts enter a fresh deployment."""
    validate_approved_sources(source_manifest, policy)
    source_by_id = {entry["id"]: entry for entry in source_manifest}
    actual = inventory(build_root)
    expected = {entry["path"]: entry["sha256"] for entry in built_manifest}
    if len(expected) != len(built_manifest):
        raise ReleaseRejected("duplicate_build_manifest_entry")
    if set(actual) != set(expected):
        raise ReleaseRejected("build_manifest_set_mismatch", unmanifested=sorted(set(actual) - set(expected)),
                              missing=sorted(set(expected) - set(actual)))
    required_public = {path for source in source_manifest if source["classification"] == "public"
                       for path in source["artifact_paths"]}
    if set(expected) != required_public:
        raise ReleaseRejected("release_not_exact_public_set", extra=sorted(set(expected) - required_public),
                              missing=sorted(required_public - set(expected)))
    for entry in built_manifest:
        source = source_by_id.get(entry["source_id"])
        if source is None or entry["path"] not in source["artifact_paths"]:
            raise ReleaseRejected("unknown_artifact_provenance", path=entry["path"])
        if source["classification"] != "public" or entry["classification"] != "public":
            raise ReleaseRejected("private_artifact_forbidden", path=entry["path"])
        if actual[entry["path"]] != entry["sha256"] or entry["sha256"] != source["sha256"]:
            raise ReleaseRejected("artifact_hash_mismatch", path=entry["path"],
                                  observed=actual[entry["path"]], approved=source["sha256"])
    deploy_root = Path(deploy_root)
    if deploy_root.exists():
        raise ReleaseRejected("deployment_must_be_fresh")
    staging = Path(tempfile.mkdtemp(prefix=".verified-release-", dir=deploy_root.parent))
    try:
        for entry in built_manifest:
            target = safe_path(staging, entry["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(safe_path(build_root, entry["path"]), target)
        if inventory(staging) != expected:
            raise ReleaseRejected("copied_artifact_integrity_mismatch")
        staging.rename(deploy_root)
    finally:
        if staging.exists():
            shutil.rmtree(staging)  # Only the freshly created staging directory is eligible.
    return {"policy_id": policy["policy_id"], "policy_sha256": digest(policy),
            "source_manifest_sha256": digest(source_manifest), "artifacts": sorted(built_manifest, key=lambda item: item["path"])}
