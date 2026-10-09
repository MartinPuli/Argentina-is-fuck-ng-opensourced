# SPDX-License-Identifier: MIT
"""Synthetic loopback-only data service. No outbound networking or LLM calls."""
import hashlib
import hmac
import ipaddress
import json
import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit


def canonical_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def require_private_bind(host):
    # Deliberately narrower than all loopback aliases: public binding is forbidden.
    if host != "127.0.0.1" or not ipaddress.ip_address(host).is_loopback:
        raise ValueError("Only literal 127.0.0.1 is permitted; public binding is forbidden")


class State:
    def __init__(self, config):
        self.mode = config["mode"]
        if self.mode not in ("no_containment", "naive_volume", "scope_only", "scope_and_revocation"):
            raise ValueError("Unknown experimental mode")
        self.contract = config["contract"]
        self.contract_digest = canonical_digest(self.contract)
        self.control_secret = config["control_secret"]
        self.tick = 0.0
        self.lock = threading.RLock()
        self.credentials = {}
        self.current_generation = {}
        for identity, token in config["initial_credentials"].items():
            self.credentials[token] = {"identity": identity, "generation": 1, "active": True}
            self.current_generation[identity] = 1
        self.requests = {identity: [] for identity in self.contract["identities"]}
        self.commands = {}
        self.telemetry = []
        self.records = [
            {"id": f"{owner}-{n:02}", "owner": owner, "value": f"FICTIONAL-{owner}-{n:02}"}
            for owner in self.contract["owners"]
            for n in range(1, self.contract["records_per_owner"] + 1)
        ]

    def read_records(self, token, query):
        with self.lock:
            credential = self.credentials.get(token)
            if credential is None or not credential["active"]:
                return 401, {"error": "invalid_or_revoked_credential"}
            identity = credential["identity"]
            if self.mode == "naive_volume":
                rule = self.contract["naive_volume_control"]
                history = [tick for tick in self.requests[identity] if tick > self.tick - rule["window_ticks"]]
                history.append(self.tick)
                self.requests[identity] = history
                if len(history) > rule["maximum_requests"]:
                    return 429, {"error": "request_volume_cutoff"}
            owner = query.get("owner", [""])[0]
            if owner not in self.contract["owners"] + ["all"]:
                return 400, {"error": "unknown_owner"}
            wanted = set(query.get("id", []))
            selected = [record for record in self.records if (owner == "all" or record["owner"] == owner)
                        and (not wanted or record["id"] in wanted)]
            if self.mode in ("scope_only", "scope_and_revocation"):
                policy = self.contract["identities"][identity]
                if owner == "all" and not policy["batch_allowed"]:
                    return 403, {"error": "batch_scope_denied"}
                if owner != "all" and owner not in policy["owners"]:
                    return 403, {"error": "owner_scope_denied"}
                if any(record["owner"] not in policy["owners"] for record in selected):
                    return 403, {"error": "owner_scope_denied"}
            return 200, {"records": selected}

    def command(self, command):
        with self.lock:
            command_id = command.get("command_id")
            if not isinstance(command_id, str) or not command_id:
                return 400, {"error": "missing_command_id"}
            digest = canonical_digest(command)
            previous = self.commands.get(command_id)
            if previous:
                if previous["digest"] != digest:
                    return 409, {"error": "command_id_conflict"}
                return 200, {**previous["response"], "duplicate": True}
            if command.get("contract_digest") != self.contract_digest:
                return 409, {"error": "contract_revision_mismatch"}
            identity = command.get("identity")
            if identity not in self.current_generation:
                return 400, {"error": "unknown_identity"}
            try:
                current = float(command["issued_at"]) <= self.tick <= float(command["expires_at"])
            except (KeyError, ValueError, TypeError):
                return 400, {"error": "invalid_command_time"}
            if not current:
                return 409, {"error": "command_expired_or_not_yet_valid"}
            generation = self.current_generation[identity]
            if command.get("expected_generation") != generation:
                return 409, {"error": "stale_credential_generation"}
            action = command.get("action")
            if action not in self.contract["permitted_response_actions"]:
                return 403, {"error": "action_outside_contract"}
            if action == "revoke_credential":
                for credential in self.credentials.values():
                    if credential["identity"] == identity and credential["generation"] == generation:
                        credential["active"] = False
                response = {"action": action, "identity": identity, "generation": generation, "revoked": True}
            else:
                generation += 1
                self.current_generation[identity] = generation
                replacement = secrets.token_urlsafe(32)
                self.credentials[replacement] = {"identity": identity, "generation": generation, "active": True}
                # Issuing a new credential deliberately does NOT revoke an older credential.
                response = {"action": action, "identity": identity, "generation": generation,
                            "credential": replacement}
            response["duplicate"] = False
            self.commands[command_id] = {"digest": digest, "response": response}
            return 200, response


def make_handler(state, plane):
    class Handler(BaseHTTPRequestHandler):
        server_version = "ReferenceDefenseLocal/1"

        def log_message(self, *_):
            pass  # Never log authorization headers or request secrets.

        def send_json(self, status, data):
            body = json.dumps(data, sort_keys=True).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def token(self):
            prefix, _, token = self.headers.get("Authorization", "").partition(" ")
            return token if prefix == "Bearer" else ""

        def do_GET(self):
            path = urlsplit(self.path)
            if path.path == "/health":
                self.send_json(200, {"healthy": True, "plane": plane})
            elif plane == "data" and path.path == "/records":
                status, body = state.read_records(self.token(), parse_qs(path.query))
                self.send_json(status, body)
            else:
                self.send_json(404, {"error": "not_found"})

        def do_POST(self):
            if plane == "control" and not hmac.compare_digest(self.token(), state.control_secret):
                self.send_json(401, {"error": "control_authentication_required"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 16384:
                    raise ValueError()
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError()
            except (ValueError, json.JSONDecodeError):
                self.send_json(400, {"error": "invalid_json_request"})
                return
            if plane == "data" and self.path == "/telemetry":
                # Text is data only; neither parsing instructions nor changing permissions occurs.
                with state.lock:
                    state.telemetry.append(str(payload.get("text", ""))[:2048])
                    state.telemetry = state.telemetry[-100:]
                self.send_json(202, {"stored_as_untrusted_data": True})
            elif plane == "control" and self.path == "/clock":
                tick = payload.get("tick")
                with state.lock:
                    if not isinstance(tick, (float, int)) or not state.tick <= tick <= 100000:
                        self.send_json(409, {"error": "invalid_or_backwards_clock"})
                    else:
                        state.tick = float(tick)
                        self.send_json(200, {"tick": state.tick})
            elif plane == "control" and self.path == "/commands":
                self.send_json(*state.command(payload))
            else:
                self.send_json(404, {"error": "not_found"})

    return Handler


def main():
    config = json.loads(sys.stdin.readline())  # Fresh credentials arrive over a pipe, never in argv or files.
    host = config.get("host", "127.0.0.1")
    require_private_bind(host)
    state = State(config)
    servers = {plane: ThreadingHTTPServer((host, 0), make_handler(state, plane)) for plane in ("data", "control")}
    for server in servers.values():
        threading.Thread(target=server.serve_forever, daemon=True).start()
    print(json.dumps({plane: server.server_address[1] for plane, server in servers.items()}), flush=True)
    try:
        for _ in sys.stdin:
            pass
    finally:
        for server in servers.values():
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
