# SPDX-License-Identifier: MIT
"""Loopback static-file serving: every deployed regular file is reachable without authentication."""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from publisher import ReleaseRejected, safe_path


def main():
    config = json.loads(sys.stdin.readline())
    if config.get("host") != "127.0.0.1":
        raise ValueError("Public binding is forbidden; only literal 127.0.0.1 is allowed")
    root = Path(config["deploy_root"]).resolve(strict=True)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            try:
                relative = unquote(urlsplit(self.path).path).removeprefix("/")
                path = safe_path(root, relative)
                resolved = path.resolve(strict=True)
                resolved.relative_to(root)
                if path.is_symlink() or not resolved.is_file():
                    raise ValueError()
                content = resolved.read_bytes()
                status = 200
            except (OSError, ValueError, ReleaseRejected):
                status, content = 404, b"not found\n"
            self.send_response(status)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(json.dumps({"port": server.server_address[1]}), flush=True)
    try:
        for _ in sys.stdin:
            pass
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
