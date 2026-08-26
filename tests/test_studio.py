import json
import socket
import threading
from http.client import HTTPConnection
from http.server import HTTPServer

from acri.config import Config, McpEntry
from acri.studio import _make_handler, serve_studio


def _running_server(config, ledger_path):
    httpd = HTTPServer(("127.0.0.1", 0), _make_handler(config, ledger_path))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def test_serves_the_dashboard_page_at_slash_studio(tmp_path):
    httpd = _running_server(Config(version=1), tmp_path / "ledger.jsonl")
    try:
        conn = HTTPConnection("127.0.0.1", httpd.server_address[1])
        conn.request("GET", "/studio")
        resp = conn.getresponse()
        assert resp.status == 200
        assert resp.getheader("Content-Type") == "text/html"
        assert b"acri studio" in resp.read()
    finally:
        httpd.shutdown()


def test_api_topology_reflects_the_config(tmp_path):
    config = Config(version=1, mcp=[McpEntry(name="github", command=["npx", "-y", "server-github"])])
    httpd = _running_server(config, tmp_path / "ledger.jsonl")
    try:
        conn = HTTPConnection("127.0.0.1", httpd.server_address[1])
        conn.request("GET", "/api/topology")
        resp = conn.getresponse()
        assert resp.status == 200
        assert resp.getheader("Content-Type") == "application/json"
        body = json.loads(resp.read())
        assert body["servers"] == [{"name": "github", "target": "npx", "sandboxed": False}]
    finally:
        httpd.shutdown()


def test_api_ledger_reads_the_real_file(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    ledger_path.write_text(json.dumps({"query": "hi", "offered": [], "selected": []}) + "\n", encoding="utf-8")
    httpd = _running_server(Config(version=1), ledger_path)
    try:
        conn = HTTPConnection("127.0.0.1", httpd.server_address[1])
        conn.request("GET", "/api/ledger")
        body = json.loads(conn.getresponse().read())
        assert body == [{"query": "hi", "offered": [], "selected": []}]
    finally:
        httpd.shutdown()


def test_returns_404_for_an_unknown_path(tmp_path):
    httpd = _running_server(Config(version=1), tmp_path / "ledger.jsonl")
    try:
        conn = HTTPConnection("127.0.0.1", httpd.server_address[1])
        conn.request("GET", "/nope")
        assert conn.getresponse().status == 404
    finally:
        httpd.shutdown()


def test_serve_studio_opens_the_existing_instance_when_the_port_is_taken(tmp_path, monkeypatch):
    """The port-in-use fallback: another `acri studio` is already running, so
    this call should open a browser at it instead of crashing."""
    config_path = tmp_path / "acri.yaml"
    config_path.write_text("version: 1\n", encoding="utf-8")
    occupied = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    occupied.bind(("127.0.0.1", 0))
    occupied.listen(1)
    port = occupied.getsockname()[1]
    try:
        opened = []
        monkeypatch.setattr("acri.studio.webbrowser.open", lambda url: opened.append(url))
        serve_studio(str(config_path), port=port)  # must return, not raise or hang
        assert opened == [f"http://127.0.0.1:{port}/studio"]
    finally:
        occupied.close()
