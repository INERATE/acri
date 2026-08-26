"""studio — `acri studio`. A read-only dashboard over acri.yaml and the ledger.

Two views: topology (servers, models, tools ever seen) and live trace
(recent ledger entries, polled). Never connects to an MCP server or calls a
model -- only reads acri.yaml and .acri/ledger.jsonl, the same two files
every other part of this project already produces. Full design and why
this is its own process/port rather than a route on `acri up`: see
docs/architecture.md #7. Ahead of decisions.md's own gate (studio was "not
built: no design exists" per the v1.1 README row) -- built at the
maintainer's request, this time written into architecture.md too. Privacy:
shows exactly what's on disk -- a RedactingLedger's `query` is already
"<redacted>" there; studio has no separate redaction logic to get wrong.
"""
from __future__ import annotations

import json
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from .studio_data import recent, topology

_PAGE = Path(__file__).parent / "studio_page.html"


def _make_handler(config: Any, ledger_path: Path) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path in ("/", "/studio"):
                body, ctype = _PAGE.read_bytes(), "text/html"
            elif self.path == "/api/topology":
                body, ctype = json.dumps(topology(config, ledger_path)).encode(), "application/json"
            elif self.path.startswith("/api/ledger"):
                body, ctype = json.dumps(recent(ledger_path)).encode(), "application/json"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args: Any) -> None:  # no request logging -- see server.py's handler
            pass

    return Handler


def serve_studio(config_path: str, ledger_path: str = ".acri/ledger.jsonl", host: str = "127.0.0.1", port: int = 8099) -> None:
    """Load acri.yaml (read-only) and block serving the dashboard. If `port` is
    already taken -- most likely another `acri studio` already running -- just
    open a browser at the existing instance instead of failing."""
    from .config import from_yaml  # lazy: needs acri[yaml], same as cli.py's _check

    config = from_yaml(config_path)
    url = f"http://{host}:{port}/studio"
    try:
        httpd = HTTPServer((host, port), _make_handler(config, Path(ledger_path)))
    except OSError:
        print(f"port {port} is already in use -- opening the existing instance instead")
        webbrowser.open(url)
        return
    webbrowser.open(url)
    print(f"acri studio: {url}")
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
