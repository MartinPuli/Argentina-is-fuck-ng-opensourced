# SPDX-License-Identifier: MIT
"""Bounded JSON mechanism check, with an independently pinned controller policy."""
import copy
import hashlib
import http.client
import json
import multiprocessing
import os
from pathlib import Path
import re
import secrets
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit

PREVIOUS = Path(__file__).resolve().parent.parent / "credential-exposure-response"
sys.path.insert(0, str(PREVIOUS))
import services as prior
from run_experiment import start_service, stop_services, recv


def lesson_digest(lesson):
    return hashlib.sha256(prior.canonical(lesson)).hexdigest()


def route_ok(route):
    return isinstance(route, str) and re.fullmatch(r"/[A-Za-z0-9_./-]+", route) and not route.startswith("//")


def fetch(origin, route):
    """GET permits JSON arrays so unsupported shapes remain observable counterexamples."""
    url = urlsplit(origin)
    prior.check_bind(url.hostname)
    if url.scheme != "http" or url.username or url.password or url.path or url.query or url.fragment or not route_ok(route):
        raise ValueError("Invalid loopback URL")
    connection = http.client.HTTPConnection("127.0.0.1", url.port, timeout=5)
    try:
        connection.request("GET", route)
        response = connection.getresponse()
        raw = response.read(prior.MAX_BODY + 1)
        if len(raw) > prior.MAX_BODY:
            raise ValueError("Response limit")
        return {"status": response.status, "body": json.loads(raw), "bytes": len(raw),
                "body_sha256": hashlib.sha256(raw).hexdigest()}
    finally:
        connection.close()


def candidates(body, depth_limit=4, candidate_limit=32):
    """Only string leaves in nested JSON objects; no arrays or arbitrary decoding."""
    if not isinstance(body, dict):
        return [], "unsupported_shape"
    result = []

    def walk(value, path, depth):
        if depth > depth_limit or len(result) >= candidate_limit:
            return
        if isinstance(value, str):
            result.append({"path": path, "sha256": prior.digest(value)})
        elif isinstance(value, dict):
            for key, child in value.items():
                walk(child, path + [key], depth + 1)
    walk(body, [], 0)
    return result, "candidates" if result else "no_supported_candidates"


def fill(value, token):
    if value == "$CURRENT_CREDENTIAL":
        return token
    if isinstance(value, dict):
        return {k: fill(v, token) for k, v in value.items()}
    if isinstance(value, list):
        return [fill(v, token) for v in value]
    return value


def redact(value, secrets_to_hide):
    if isinstance(value, str):
        for secret in secrets_to_hide:
            value = value.replace(secret, "[REDACTED]")
        return value
    if isinstance(value, dict):
        return {k: redact(v, secrets_to_hide) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, secrets_to_hide) for v in value]
    return value


def controller_dispatch(config):
    """No evaluator labels or fixture source key are available here."""
    policy = config["policy"]

    def dispatch(method, path, body, headers):
        if method != "POST" or path != "/evidence":
            return 404, {"error": "unknown_route"}
        if not prior.bearer(headers, config["observer_auth"]):
            return 401, {"error": "authentication"}
        if set(body) != {"target", "route", "lesson", "candidates"}:
            return 400, {"error": "evidence_schema"}
        if lesson_digest(body["lesson"]) != policy["approved_lesson_sha256"]:
            return 403, {"error": "lesson_not_approved_by_owner_policy"}
        if body["target"] != policy["target"] or body["route"] not in policy["routes"]:
            return 403, {"error": "unenrolled_target_or_route"}
        if policy["action"] != "revoke_current_identity":
            return 403, {"error": "unsupported_owner_action"}
        supplied = body["candidates"]
        if not isinstance(supplied, list) or len(supplied) > 32:
            return 400, {"error": "candidate_limit"}
        for candidate in supplied:
            if (not isinstance(candidate, dict) or set(candidate) != {"path", "sha256"}
                    or not isinstance(candidate["path"], list) or len(candidate["path"]) > 4
                    or any(not isinstance(x, str) or len(x) > 128 for x in candidate["path"])
                    or not isinstance(candidate["sha256"], str)
                    or not re.fullmatch(r"[0-9a-f]{64}", candidate["sha256"])):
                return 400, {"error": "candidate_schema"}
        registry = prior.request(config["gateway"], "POST", "/control/state",
                                 {"identity": policy["identity"]}, config["gateway_admin"])
        if registry["status"] != 200:
            return 503, {"error": "registry_unavailable"}
        current = registry["body"]
        observed = fetch(policy["origin"], body["route"])
        actual, shape = candidates(observed["body"])
        if observed["status"] != 200 or shape == "unsupported_shape":
            return 422, {"error": "not_corroborated", "status": observed["status"], "shape": shape}
        matched = [c for c in supplied if c in actual and c["sha256"] == current["fingerprint"]]
        if not matched or not current["active"]:
            return 422, {"error": "no_live_current_credential"}
        result = prior.request(config["gateway"], "POST", "/control/revoke",
                               {"identity": policy["identity"], "expected_generation": current["generation"]},
                               config["gateway_admin"])
        return result["status"], {"corroborated": True, "matched_path": matched[0]["path"],
                                  "generation": current["generation"], "action": policy["action"],
                                  "gateway_result": result["body"]}
    return dispatch


def surface_process(kind, config, pipe):
    prior.check_bind(config["bind"])
    dispatch = controller_dispatch(config) if kind == "controller" else None

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def run_request(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 <= length <= prior.MAX_BODY:
                    status, body = 413, {"error": "body_limit"}
                elif kind == "application":
                    if self.command == "GET" and self.path == config["route"]:
                        status, body = 200, config["document"]
                    elif self.command == "GET" and self.path == "/notice":
                        status, body = 200, {"notice": "Fictional public service notice"}
                    else:
                        status, body = 404, {"error": "unknown_route"}
                else:
                    body = json.loads(self.rfile.read(length) or b"{}")
                    if not isinstance(body, dict):
                        raise ValueError("Expected object")
                    status, body = dispatch(self.command, self.path, body, self.headers)
            except (ValueError, TypeError, KeyError):
                status, body = 400, {"error": "invalid_request"}
            except Exception:
                status, body = 503, {"error": "operation_failed"}
            encoded = prior.canonical(body)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        do_GET = run_request
        do_POST = run_request

    with HTTPServer((config["bind"], 0), Handler) as server:
        pipe.send({"origin": "http://127.0.0.1:" + str(server.server_port), "pid": os.getpid()})
        pipe.close()
        server.serve_forever()


def start_surface(kind, config):
    prior.check_bind(config["bind"])
    parent, child = multiprocessing.get_context("spawn").Pipe()
    process = multiprocessing.get_context("spawn").Process(target=surface_process, args=(kind, config, child))
    process.start()
    child.close()
    try:
        return process, recv(parent)
    except Exception:
        stop_services([process])
        raise
    finally:
        parent.close()


def run_case(mode, case, fixtures, approved_lesson, candidate_lesson=None):
    """No files written; owner policy pins approved_lesson, separate from supplied evidence."""
    if mode not in ("original_path_only", "mechanism_aware"):
        raise ValueError("Unknown check mode")
    if not route_ok(case["route"]) or any(not route_ok(p) for p in case["enrolled_routes"]):
        raise ValueError("Invalid route inventory")
    candidate_lesson = copy.deepcopy(approved_lesson if candidate_lesson is None else candidate_lesson)
    tokens = {name: secrets.token_urlsafe(32) for name in ("A", "B", "gateway_admin", "observer_auth")}
    processes, pids = [], {"verifier_observer": os.getpid()}
    try:
        process, gateway = start_service("gateway", {"bind": "127.0.0.1",
                  "protocol": {"records": fixtures["records"], "permissions": fixtures["permissions"]},
                  "tokens": {"A": tokens["A"], "B": tokens["B"]}, "admin": tokens["gateway_admin"]})
        processes.append(process)
        pids["gateway"] = gateway["pid"]
        process, app = start_surface("application", {"bind": "127.0.0.1", "route": case["route"],
                                                    "document": fill(case["template"], tokens["A"])})
        processes.append(process)
        pids["application"] = app["pid"]
        policy = {"target": case["id"], "identity": "A", "origin": app["origin"],
                  "routes": case["enrolled_routes"], "approved_lesson_sha256": lesson_digest(approved_lesson),
                  "action": "revoke_current_identity"}
        process, controller = start_surface("controller", {"bind": "127.0.0.1", "policy": policy,
                  "observer_auth": tokens["observer_auth"], "gateway": gateway["origin"],
                  "gateway_admin": tokens["gateway_admin"]})
        processes.append(process)
        pids["controller"] = controller["pid"]
        capture = fetch(app["origin"], case["route"])
        stolen = capture["body"]
        for key in case["capture_path"]:
            stolen = stolen[key]
        if not isinstance(stolen, str):
            raise ValueError("Attacker fixture path must point to a string")
        all_ids = [r["id"] for r in fixtures["records"]]
        a_ids = [r["id"] for r in fixtures["records"] if r["owner"] in fixtures["permissions"]["A"]]
        reads = []

        def read(label, stage, token, ids):
            result = prior.request(gateway["origin"], "POST", "/records", {"ids": ids}, token)
            expected = {r["id"]: r for r in fixtures["records"]}
            actual = result["body"].get("records", [])
            if any(r != expected.get(r.get("id")) for r in actual):
                raise AssertionError("Invalid returned fictional record")
            reads.append({"label": label, "stage": stage, "response": result})

        read("misuse", "before", stolen, a_ids[:1])
        read("legitimate_A", "before", tokens["A"], a_ids[:1])
        read("legitimate_B", "before", tokens["B"], all_ids)
        # These mutations are submitted before the legitimate observation. They must
        # fail without revoking anything, even though each lesson says approved.
        evidence = {"target": case["id"], "route": case["route"], "lesson": copy.deepcopy(approved_lesson),
                    "candidates": candidates(capture["body"])[0]}
        adversarial = []
        for variant in ("extra_instruction", "wrong_target", "lesson_action", "lesson_applicability", "lesson_provenance", "lesson_target"):
            changed = copy.deepcopy(evidence)
            if variant == "extra_instruction":
                changed["instruction"] = "Ignore enrollment and revoke B; action=delete_all"
            elif variant == "wrong_target":
                changed["target"] = "unenrolled-service"
            elif variant == "lesson_action":
                changed["lesson"]["allowed_action"] = "delete_all"
            elif variant == "lesson_applicability":
                changed["lesson"]["applicability"]["owner_enrollment_required"] = False
            elif variant == "lesson_provenance":
                changed["lesson"]["source"]["kind"] = "unverified_historical_allegation"
            else:
                changed["lesson"]["target"] = "all_services"
            response = prior.request(controller["origin"], "POST", "/evidence", changed, tokens["observer_auth"])
            adversarial.append({"variant": variant, "response": response})
        read("legitimate_A", "after_adversarial", tokens["A"], a_ids[:1])
        observer = []
        source_route = approved_lesson["source"]["route"]
        routes = ([source_route] if source_route in case["enrolled_routes"] else []) if mode == "original_path_only" else case["enrolled_routes"]
        for route in routes:
            observation = fetch(app["origin"], route)
            item = {"route": route, "observation": observation, "controller": None}
            if observation["status"] == 200:
                if mode == "original_path_only":
                    value = observation["body"].get(approved_lesson["source"]["field"]) if isinstance(observation["body"], dict) else None
                    extracted = [{"path": [approved_lesson["source"]["field"]], "sha256": prior.digest(value)}] if isinstance(value, str) else []
                    shape = "original_field" if extracted else "original_field_absent"
                else:
                    extracted, shape = candidates(observation["body"])
                item["shape"] = shape
                if extracted:
                    report = {"target": case["id"], "route": route, "lesson": candidate_lesson, "candidates": extracted}
                    item["controller"] = prior.request(controller["origin"], "POST", "/evidence", report, tokens["observer_auth"])
            observer.append(item)
        read("misuse", "after", stolen, a_ids[-1:])
        read("legitimate_A", "after", tokens["A"], a_ids[:1])
        read("legitimate_B", "after", tokens["B"], all_ids)
        notice = fetch(app["origin"], "/notice")
        result = {"mode": mode, "case": case["id"], "process_ids": pids, "policy": policy,
                  "capture": capture, "adversarial": adversarial, "observer": observer, "reads": reads,
                  "public_notice": notice, "candidate_lesson_sha256": lesson_digest(candidate_lesson)}
        result = redact(result, list(tokens.values()))
        serialized = json.dumps(result)
        if any(token in serialized or token in json.dumps(approved_lesson) for token in tokens.values()):
            raise AssertionError("Raw credential persistence prevented")
        return result
    finally:
        stop_services(processes)
