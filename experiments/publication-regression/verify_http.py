# SPDX-License-Identifier: MIT
"""Independent client process: evaluate actual unauthenticated HTTP response bytes."""
import base64
import hashlib
import json
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import ProxyHandler, Request, build_opener


def verify(config):
    if config.get("host") != "127.0.0.1":
        raise ValueError("Only loopback HTTP is permitted")
    port = config["port"]
    if not isinstance(port, int) or not 0 < port < 65536:
        raise ValueError("Invalid local port")
    opener = build_opener(ProxyHandler({}))
    fixture = config["fixture"]
    private = [entry for entry in fixture["sources"] if entry.get("classification") == "private"]
    public = {path: entry["content"].encode() for entry in fixture["sources"] if entry.get("classification") == "public"
              for path in entry["artifact_paths"]}
    root = Path(config["deploy_root"])
    # Read the actual deployment filesystem, not a publisher-provided counter or inventory.
    physical = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in root.rglob("*") if path.is_file()}
    paths = sorted({path for entry in fixture["sources"] for path in entry["artifact_paths"]}
                   | set(physical) | set(fixture.get("probe_paths", [])))
    observations = []
    for path in paths:
        request = Request(f"http://127.0.0.1:{port}/" + quote(path, safe="/"))
        try:
            response = opener.open(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            body, status = response.read(), response.status
        matches = []
        for entry in private:
            payload = entry["content"].encode()
            marker = entry.get("private_marker", "").encode()
            if (payload and payload in body) or (marker and marker in body):
                matches.append({"source_id": entry["id"], "exact_full_content": body == payload,
                                "contains_full_content": bool(payload and payload in body),
                                "contains_marker": bool(marker and marker in body)})
        observations.append({"path": path, "status": status, "body_bytes": len(body),
                             "body_sha256": hashlib.sha256(body).hexdigest(),
                             "body_base64": base64.b64encode(body).decode(),
                             "private_matches": matches,
                             "expected_public": path in public,
                             "public_exact_success": path in public and status == 200 and body == public[path]})
    manifest = config.get("release_manifest")
    exact_set = None
    manifest_http_exact = None
    if manifest is not None:
        expected = {entry["path"]: entry["sha256"] for entry in manifest["artifacts"]}
        exact_set = physical == expected
        actual_http = {item["path"]: item["body_sha256"] for item in observations if item["status"] == 200}
        manifest_http_exact = actual_http == expected
    return {"observations": observations, "deploy_inventory_independently_read": physical,
            "release_manifest_exact_artifact_set": exact_set, "release_manifest_exact_http_set": manifest_http_exact,
            "metrics": {
                "unauthenticated_requests": len(observations),
                "private_exposing_responses": sum(bool(item["private_matches"]) for item in observations),
                "private_source_ids_exposed": sorted({match["source_id"] for item in observations for match in item["private_matches"]}),
                "private_exact_content_responses": sum(any(match["exact_full_content"] for match in item["private_matches"]) for item in observations),
                "public_requests": len(public),
                "public_exact_successes": sum(item["public_exact_success"] for item in observations)
            }}


if __name__ == "__main__":
    print(json.dumps(verify(json.loads(sys.stdin.read())), sort_keys=True))
