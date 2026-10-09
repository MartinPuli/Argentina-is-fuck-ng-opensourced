# SPDX-License-Identifier: MIT
"""Owned loopback-only experiment services; all credentials stay in memory."""
from __future__ import annotations
import hashlib
import hmac
import http.client
import json
import multiprocessing
import os
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

TIMEOUT = 8
MAX_BODY = 65536
MODES = ("entry_only", "output_generation")


def encode(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def record_line(record):
    return encode({"type": "record", "record": record}) + b"\n"


def connection(origin):
    parsed = urlsplit(origin)
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or not parsed.port or parsed.path not in ("", "/") or parsed.query or parsed.fragment or parsed.username:
        raise ValueError("Only literal loopback HTTP origins are supported")
    return http.client.HTTPConnection("127.0.0.1", parsed.port, timeout=TIMEOUT)


def request(origin, path, token, payload=None, method="POST"):
    conn = connection(origin)
    try:
        body = None if payload is None else encode(payload)
        conn.request(method, path, body, {"Authorization": "Bearer " + token, "Content-Type": "application/json"})
        response = conn.getresponse()
        raw = response.read(MAX_BODY + 1)
        if len(raw) > MAX_BODY:
            raise ValueError("Response exceeds bound")
        return response.status, raw
    finally:
        conn.close()


def fresh_credentials(identities):
    return {key: secrets.token_urlsafe(32) for key in list(identities) + ["gateway_admin", "coordinator", "controller_command"]}


def start_service(kind, config, context=None):
    context = context or multiprocessing.get_context("spawn")
    receive, send = context.Pipe(duplex=False)
    process = context.Process(target=_serve, args=(kind, config, send), daemon=True)
    process.start()
    send.close()
    if not receive.poll(TIMEOUT):
        process.terminate()
        process.join(TIMEOUT)
        receive.close()
        raise RuntimeError("Service startup timed out")
    metadata = receive.recv()
    receive.close()
    if "error" in metadata:
        process.join(TIMEOUT)
        raise RuntimeError(metadata["error"])
    return process, metadata


def stop_services(processes):
    for process in reversed(processes):
        if process.is_alive():
            process.terminate()
        process.join(TIMEOUT)
        if process.is_alive():
            process.kill()
            process.join(TIMEOUT)
    return all(not process.is_alive() for process in processes)


def _serve(kind, config, ready):
    try:
        if config.get("bind", "127.0.0.1") != "127.0.0.1":
            raise ValueError("Public binding is forbidden")
        if kind not in ("gateway", "controller"):
            raise ValueError("Unknown service")
        if kind == "gateway" and config["mode"] not in MODES:
            raise ValueError("Unknown enforcement mode")
        # This mutex covers checks AND protected writes/flushes AND the gateway ACK.
        gate = threading.Lock()
        state_lock = threading.Lock()
        identities = {name: {"generation": 1, "active": True, "token": token} for name, token in config.get("identity_tokens", {}).items()}
        records = {record["id"]: record for record in config.get("records", [])}
        streams, jobs = {}, {}
        boundary = {"sequence": 0}

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.0"

            def log_message(self, *_args):
                pass

            def setup(self):
                super().setup()
                self.connection.settimeout(TIMEOUT)

            def authorized(self, token):
                supplied = self.headers.get("Authorization", "")
                return hmac.compare_digest(supplied, "Bearer " + token)

            def send_json(self, status, body):
                raw = encode(body)
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(raw)
                self.wfile.flush()

            def body(self):
                length = int(self.headers.get("Content-Length", "0"))
                if length < 0 or length > MAX_BODY:
                    raise ValueError("Invalid body size")
                value = json.loads(self.rfile.read(length) or b"{}")
                if not isinstance(value, dict):
                    raise ValueError("Expected object")
                return value

            def admit(self, body):
                with gate:
                    identity = next((name for name, auth in identities.items() if self.authorized(auth["token"])), None)
                    if identity is None or not identities[identity]["active"]:
                        return None, 401
                    ids = body.get("ids")
                    if not isinstance(ids, list) or not 1 <= len(ids) <= 64 or any(not isinstance(item, str) for item in ids):
                        return None, 400
                    if any(item not in records or records[item]["owner"] != identity for item in ids):
                        return None, 403
                    return {"identity": identity, "generation": identities[identity]["generation"], "ids": ids}, 200

            def stream_headers(self):
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()

            def emit_records(self, context, ids):
                for record_id in ids:
                    with gate:
                        auth = identities[context["identity"]]
                        if config["mode"] == "output_generation" and (not auth["active"] or auth["generation"] != context["generation"]):
                            self.wfile.write(encode({"type": "denied", "reason": "admitted_generation_revoked"}) + b"\n")
                            self.wfile.flush()
                            return False
                        # Do not move this write or flush outside the mutex.
                        self.wfile.write(record_line(records[record_id]))
                        self.wfile.flush()
                        boundary["sequence"] += 1
                return True

            def finish_stream(self):
                self.wfile.write(encode({"type": "complete"}) + b"\n")
                self.wfile.flush()

            def do_POST(self):
                try:
                    self.dispatch(self.body())
                except (ValueError, TypeError, KeyError):
                    self.send_json(400, {"error": "invalid_request"})
                except (BrokenPipeError, ConnectionResetError, TimeoutError):
                    self.close_connection = True

            def dispatch(self, body):
                if kind == "controller":
                    if self.path != "/revoke" or not self.authorized(config["command_token"]):
                        return self.send_json(403, {"error": "forbidden"})
                    if set(body) != {"identity", "expected_generation"} or body["identity"] != config["enrolled_identity"]:
                        return self.send_json(403, {"error": "outside_enrollment"})
                    status, raw = request(config["gateway_origin"], "/control/revoke", config["gateway_admin"], body)
                    # Controller acknowledges only after observing the gateway's ACK.
                    return self.send_json(status, {"gateway_ack": json.loads(raw), "controller_pid": os.getpid()})

                if self.path == "/control/revoke":
                    if not self.authorized(config["gateway_admin"]):
                        return self.send_json(403, {"error": "forbidden"})
                    if set(body) != {"identity", "expected_generation"} or body["identity"] not in identities:
                        return self.send_json(400, {"error": "invalid_target"})
                    with gate:
                        auth = identities[body["identity"]]
                        if not auth["active"] or auth["generation"] != body["expected_generation"]:
                            return self.send_json(409, {"error": "stale_generation"})
                        auth["active"] = False
                        auth["generation"] += 1
                        # ACK bytes are also written/flushed under the output mutex.
                        return self.send_json(200, {"revoked": True, "identity": body["identity"], "generation": auth["generation"], "boundary_sequence": boundary["sequence"], "gateway_pid": os.getpid()})

                if self.path.startswith("/sync/"):
                    if not self.authorized(config["coordinator"]):
                        return self.send_json(403, {"error": "forbidden"})
                    with state_lock:
                        stream = streams.get(body.get("stream_id"))
                        job = jobs.get(body.get("job_id"))
                    if self.path == "/sync/wait-stream" and stream:
                        if not stream["paused"].wait(TIMEOUT):
                            return self.send_json(504, {"error": "barrier_timeout"})
                        return self.send_json(200, {"paused": True})
                    if self.path == "/sync/release-stream" and stream and stream["paused"].is_set():
                        stream["release"].set()
                        return self.send_json(200, {"released": True})
                    if self.path == "/sync/release-job" and job:
                        job["release"].set()
                        return self.send_json(200, {"released": True})
                    return self.send_json(400, {"error": "unknown_barrier"})

                if self.path == "/job-result":
                    with state_lock:
                        job = jobs.get(body.get("job_id"))
                    if job is None or not self.authorized(job["ticket"]):
                        return self.send_json(403, {"error": "invalid_job_capability"})
                    if not job["ready"].wait(TIMEOUT):
                        return self.send_json(504, {"error": "job_timeout"})
                    self.stream_headers()
                    if self.emit_records(job["context"], job["context"]["ids"]):
                        self.finish_stream()
                    return

                if self.path not in ("/read", "/stream", "/queue"):
                    return self.send_json(404, {"error": "not_found"})
                context, status = self.admit(body)
                if context is None:
                    return self.send_json(status, {"error": "not_authorized"})
                if self.path == "/read":
                    self.stream_headers()
                    if self.emit_records(context, context["ids"]):
                        self.finish_stream()
                    return
                if self.path == "/stream":
                    stream_id, prefix = body.get("stream_id"), body.get("prefix_chunks")
                    if not isinstance(stream_id, str) or len(stream_id) > 80 or not isinstance(prefix, int) or not 1 <= prefix < len(context["ids"]):
                        return self.send_json(400, {"error": "invalid_stream"})
                    stream = {"paused": threading.Event(), "release": threading.Event()}
                    with state_lock:
                        if stream_id in streams:
                            return self.send_json(409, {"error": "duplicate_stream"})
                        streams[stream_id] = stream
                    self.stream_headers()
                    if not self.emit_records(context, context["ids"][:prefix]):
                        return
                    stream["paused"].set()
                    if not stream["release"].wait(TIMEOUT):
                        self.wfile.write(encode({"type": "error", "reason": "barrier_timeout"}) + b"\n")
                        self.wfile.flush()
                        return
                    if self.emit_records(context, context["ids"][prefix:]):
                        self.finish_stream()
                    return
                job_id = secrets.token_hex(16)
                job = {"context": context, "ticket": secrets.token_urlsafe(32), "release": threading.Event(), "ready": threading.Event()}
                with state_lock:
                    jobs[job_id] = job

                def compute():
                    if job["release"].wait(TIMEOUT):
                        # Minimal queued computation; output still needs its own gate.
                        job["computed_digest"] = hashlib.sha256(encode([records[item] for item in context["ids"]])).hexdigest()
                        job["ready"].set()

                threading.Thread(target=compute, daemon=True).start()
                return self.send_json(202, {"job_id": job_id, "ticket": job["ticket"], "state": "accepted_waiting"})

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.daemon_threads = True
        ready.send({"origin": "http://127.0.0.1:" + str(server.server_port), "pid": os.getpid()})
        ready.close()
        server.serve_forever(poll_interval=0.1)
    except Exception as exc:
        try:
            ready.send({"error": type(exc).__name__})
            ready.close()
        except (BrokenPipeError, OSError):
            pass
        raise
