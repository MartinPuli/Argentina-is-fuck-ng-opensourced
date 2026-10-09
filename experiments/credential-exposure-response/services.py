# SPDX-License-Identifier: MIT
"""Synthetic loopback services. No tokens or request bodies are logged or saved."""
import hashlib
import http.client
import json
import os
import re
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit

MAX_BODY = 65536
MODES = ("scope_only", "repair_only", "revoke_only", "combined")


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def check_bind(host):
    if host != "127.0.0.1":
        raise ValueError("Only literal 127.0.0.1 is permitted; never tunnel this fixture")


def request(origin, method, path, body=None, token=None):
    """No proxy, DNS lookup, redirects or external host; bounded synchronous HTTP."""
    url = urlsplit(origin)
    check_bind(url.hostname)
    if url.scheme != "http" or url.username or url.password or url.path or url.query or url.fragment:
        raise ValueError("Invalid local origin")
    if not path.startswith("/") or path.startswith("//"):
        raise ValueError("Invalid local path")
    payload = None if body is None else canonical(body)
    if payload and len(payload) > MAX_BODY:
        raise ValueError("Request too large")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    connection = http.client.HTTPConnection("127.0.0.1", url.port, timeout=5)
    try:
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse()
        raw = response.read(MAX_BODY + 1)
        if len(raw) > MAX_BODY:
            raise ValueError("Response too large")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Expected response object")
        return {"status": response.status, "body": data, "bytes": len(raw),
                "body_sha256": hashlib.sha256(raw).hexdigest()}
    finally:
        connection.close()


def bearer(headers, expected):
    return secrets.compare_digest(headers.get("Authorization", ""), "Bearer " + expected)


def serve(kind, config, pipe):
    """Spawn target: each service receives only its own configuration via a pipe."""
    check_bind(config["bind"])
    dispatch = {"gateway": gateway, "app": application, "controller": controller}[kind](config)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def handle_request(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 0 or length > MAX_BODY:
                    status, body = 413, {"error": "oversized_request"}
                else:
                    raw = self.rfile.read(length) if length else b"{}"
                    data = json.loads(raw)
                    if not isinstance(data, dict):
                        raise ValueError("Expected object")
                    status, body = dispatch(self.command, self.path, data, self.headers)
            except (ValueError, TypeError, KeyError):
                status, body = 400, {"error": "invalid_request"}
            except Exception:
                # Deliberately omit exception text; it could contain credential material.
                status, body = 503, {"error": "operation_failed"}
            encoded = canonical(body)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        do_GET = handle_request
        do_POST = handle_request

    with HTTPServer((config["bind"], 0), Handler) as server:
        pipe.send({"origin": "http://127.0.0.1:" + str(server.server_port), "pid": os.getpid()})
        pipe.close()
        server.serve_forever()


def gateway(config):
    records = {r["id"]: r for r in config["protocol"]["records"]}
    permissions = config["protocol"]["permissions"]
    current = {identity: 1 for identity in config["tokens"]}
    credentials = {token: {"identity": identity, "generation": 1, "active": True}
                   for identity, token in config["tokens"].items()}

    def dispatch(method, path, body, headers):
        if method == "POST" and path == "/records":
            authorization = headers.get("Authorization", "")
            token = authorization[7:] if authorization.startswith("Bearer ") else ""
            entry = credentials.get(token)
            if not entry or not entry["active"]:
                return 401, {"error": "credential_not_active", "records": []}
            ids = body.get("ids")
            if not isinstance(ids, list) or len(ids) > 1000 or any(not isinstance(i, str) for i in ids):
                return 400, {"error": "invalid_ids", "records": []}
            if any(i not in records for i in ids):
                return 404, {"error": "unknown_record", "records": []}
            allowed = permissions[entry["identity"]]
            if any(records[i]["owner"] not in allowed for i in ids):
                return 403, {"error": "owner_scope", "records": []}
            return 200, {"records": [records[i] for i in ids]}
        if method != "POST" or path not in ("/control/state", "/control/revoke", "/control/issue"):
            return 404, {"error": "unknown_route"}
        if not bearer(headers, config["admin"]):
            return 401, {"error": "control_authentication"}
        identity = body.get("identity")
        if identity not in current:
            return 404, {"error": "unknown_identity"}
        generation = current[identity]
        token, entry = next((t, e) for t, e in credentials.items()
                            if e["identity"] == identity and e["generation"] == generation)
        if path == "/control/state":
            return 200, {"identity": identity, "generation": generation,
                         "fingerprint": digest(token), "active": entry["active"]}
        if type(body.get("expected_generation")) is not int or body["expected_generation"] != generation:
            return 409, {"error": "stale_generation"}
        if path == "/control/revoke":
            entry["active"] = False
            return 200, {"revoked_generation": generation, "identity": identity}
        new_token = secrets.token_urlsafe(32)
        current[identity] += 1
        credentials[new_token] = {"identity": identity, "generation": generation + 1, "active": True}
        return 200, {"identity": identity, "generation": generation + 1, "credential": new_token}
    return dispatch


def application(config):
    state = {"credential": config["credential"], "generation": 1, "exposed": True}

    def dispatch(method, path, body, headers):
        if method == "GET" and path == config["route"]:
            if not state["exposed"]:
                return 404, {"error": "route_removed"}
            return 200, {"identity": config["identity"], "generation": state["generation"],
                         "credential": state["credential"]}
        if method == "POST" and path == "/use":
            if not bearer(headers, config["client"]):
                return 401, {"error": "client_authentication"}
            result = request(config["gateway"], "POST", "/records", body, state["credential"])
            return result["status"], result["body"]
        if method != "POST" or path not in ("/control/repair", "/control/replace"):
            return 404, {"error": "unknown_route"}
        if not bearer(headers, config["admin"]):
            return 401, {"error": "control_authentication"}
        if path == "/control/repair":
            state["exposed"] = False
            return 200, {"route_removed": True}
        if type(body.get("generation")) is not int or body["generation"] != state["generation"] + 1:
            return 409, {"error": "stale_generation"}
        if not isinstance(body.get("credential"), str) or len(body["credential"]) < 32:
            return 400, {"error": "invalid_credential"}
        state.update(credential=body["credential"], generation=body["generation"])
        return 200, {"provisioned_generation": state["generation"]}
    return dispatch


def controller(config):
    mode = config["mode"]
    if mode not in MODES:
        raise ValueError("Unknown response mode")
    responses, recoveries = {}, {}
    identity = config["identity"]

    def gateway_call(path, body):
        return request(config["gateway"], "POST", path, body, config["gateway_admin"])

    def dispatch(method, path, body, headers):
        if method != "POST" or path not in ("/evidence", "/recover"):
            return 404, {"error": "unknown_route"}
        expected = config["observer"] if path == "/evidence" else config["recovery"]
        if not bearer(headers, expected):
            return 401, {"error": "controller_authentication"}
        if path == "/recover":
            if set(body) != {"operation_id", "expected_generation"}:
                return 400, {"error": "recovery_shape"}
            op = body["operation_id"]
            if not isinstance(op, str) or not 1 <= len(op) <= 64:
                return 400, {"error": "operation_id"}
            if op in recoveries:
                previous, answer = recoveries[op]
                if previous != body:
                    return 409, {"error": "idempotency_conflict"}
                return 200, dict(answer, duplicate=True)
            issued = gateway_call("/control/issue", {"identity": identity,
                                  "expected_generation": body["expected_generation"]})
            if issued["status"] != 200:
                return issued["status"], issued["body"]
            replacement = issued["body"]
            provisioned = request(config["app"], "POST", "/control/replace",
                                  {"generation": replacement["generation"],
                                   "credential": replacement["credential"]}, config["app_admin"])
            if provisioned["status"] != 200:
                return 503, {"error": "provision_failed_after_issue"}
            answer = {"generation": replacement["generation"], "provisioned": True}
            recoveries[op] = (dict(body), answer)
            return 200, answer

        fields = {"observation_id", "target", "origin", "route", "generation", "fingerprint"}
        if set(body) != fields:
            return 400, {"error": "evidence_shape"}
        op = body["observation_id"]
        if not isinstance(op, str) or not 1 <= len(op) <= 64:
            return 400, {"error": "observation_id"}
        if body["target"] != identity or body["origin"] != config["app"] or body["route"] != config["route"]:
            return 403, {"error": "unenrolled_target_or_route"}
        if type(body["generation"]) is not int or not isinstance(body["fingerprint"], str) or not re.fullmatch(r"[a-f0-9]{64}", body["fingerprint"]):
            return 400, {"error": "evidence_value"}
        if op in responses:
            previous, answer = responses[op]
            if previous != body:
                return 409, {"error": "idempotency_conflict"}
            return 200, dict(answer, duplicate=True)
        registry = gateway_call("/control/state", {"identity": identity})
        if registry["status"] != 200:
            return 503, {"error": "registry_unavailable"}
        current = registry["body"]
        if body["generation"] != current["generation"]:
            return 409, {"error": "stale_generation"}
        observed = request(config["app"], "GET", config["route"])
        if observed["status"] != 200:
            return 422, {"error": "exposure_not_corroborated", "observation_status": observed["status"]}
        exposed = observed["body"]
        if (exposed.get("identity") != identity or exposed.get("generation") != current["generation"]
                or not isinstance(exposed.get("credential"), str)
                or digest(exposed["credential"]) != current["fingerprint"]
                or body["fingerprint"] != current["fingerprint"]):
            return 422, {"error": "credential_mismatch"}
        if not current["active"]:
            return 409, {"error": "generation_already_revoked"}
        steps = []
        if mode in ("revoke_only", "combined"):
            result = gateway_call("/control/revoke", {"identity": identity,
                                  "expected_generation": current["generation"]})
            steps.append({"operation": "revoke", "status": result["status"]})
            if result["status"] != 200:
                return 503, {"error": "revoke_failed", "steps": steps}
        if mode in ("repair_only", "combined"):
            result = request(config["app"], "POST", "/control/repair", {}, config["app_admin"])
            steps.append({"operation": "remove_exposure_route", "status": result["status"]})
            if result["status"] != 200:
                return 503, {"error": "repair_failed", "steps": steps}
        answer = {"corroborated": True, "generation": current["generation"],
                  "corroboration_http_status": observed["status"], "steps": steps, "mode": mode}
        responses[op] = (dict(body), answer)
        return 200, answer
    return dispatch


def sanitized_exposure(response):
    body = response["body"]
    if "credential" not in body:
        return response
    return {**response, "body": {"identity": body.get("identity"), "generation": body.get("generation"),
                                "credential": "[REDACTED]"}}


def observe(config, observation_id):
    observed = request(config["app"], "GET", config["route"])
    answer = {"observation": sanitized_exposure(observed), "evidence": None, "controller": None}
    if observed["status"] != 200 or not isinstance(observed["body"].get("credential"), str):
        return answer
    body = observed["body"]
    evidence = {"observation_id": observation_id, "target": config["identity"],
                "origin": config["app"], "route": config["route"],
                "generation": body.get("generation"), "fingerprint": digest(body["credential"])}
    answer["evidence"] = evidence
    answer["controller"] = request(config["controller"], "POST", "/evidence", evidence, config["observer"])
    return answer


def observer_process(config, pipe):
    """Observer can only read the app and report metadata, not repair or revoke directly."""
    pipe.send({"pid": os.getpid()})
    while True:
        try:
            message = pipe.recv()
        except EOFError:
            break
        if message is None:
            break
        try:
            pipe.send(observe(config, message["observation_id"]))
        except Exception:
            pipe.send({"error": "observation_failed"})
    pipe.close()
