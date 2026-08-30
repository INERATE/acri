import json
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from types import SimpleNamespace

from acri.config import Config
from acri.corpus import Tool, index
from acri.server import _make_handler


def _client(create_fn):
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create_fn)))


def _running_server(handler_cls):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def test_serves_an_sse_response_over_a_real_socket():
    def create(**kwargs):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="hello", tool_calls=None))])

    corpus = index([Tool(name="noop", description="does nothing")])
    handler_cls = _make_handler(Config(version=1), corpus, _client(create), "openai", None, ledger=None)
    httpd = _running_server(handler_cls)
    try:
        conn = HTTPConnection("127.0.0.1", httpd.server_address[1])
        body = json.dumps({"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}]})
        conn.request("POST", "/v1/chat/completions", body=body, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        raw = resp.read().decode()

        assert resp.status == 200
        assert resp.getheader("Content-Type") == "text/event-stream"
        lines = [l for l in raw.split("\n\n") if l]
        chunk = json.loads(lines[0][len("data: "):])
        assert chunk["choices"][0]["delta"]["content"] == "hello"
        assert lines[-1] == "data: [DONE]"
    finally:
        httpd.shutdown()


def test_returns_404_for_an_unknown_path():
    corpus = index([Tool(name="noop", description="does nothing")])
    handler_cls = _make_handler(Config(version=1), corpus, _client(lambda **kw: None), "openai", None, ledger=None)
    httpd = _running_server(handler_cls)
    try:
        conn = HTTPConnection("127.0.0.1", httpd.server_address[1])
        conn.request("POST", "/nope", body="{}")
        assert conn.getresponse().status == 404
    finally:
        httpd.shutdown()
