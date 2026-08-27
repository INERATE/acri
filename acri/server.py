"""server — `acri up`. Binds an OpenAI-compatible /v1/chat/completions endpoint.

Built at the maintainer's explicit request, ahead of decisions.md's own gate
("built after users want it, not before") -- on record in the commit
message, not silently assumed.

stdlib http.server only: no FastAPI/uvicorn. SSE is wire-level -- one
blocking acri.run() call, chunked as a single event, not a true stream
(port.py doesn't support that yet).
"""
from __future__ import annotations

import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .builtin import resolve_builtin
from .config import Config, from_yaml
from .credentials import missing_env_vars, provider_for
from .corpus import index
from .daemon import RedactingLedger, default_ledger, handle_chat_completion
from .mcp_connect import connect_all
from .studio_data import write_corpus_snapshot


def _client_for(provider: str) -> Any:
    if provider == "gemini":
        from google import genai

        return genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    import openai

    return openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def _make_handler(config: Config, corpus: Any, client: Any, provider: str, ledger: Any) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            if self.path != "/v1/chat/completions":
                self.send_error(404)
                return
            length = int(self.headers.get("Content-Length", 0))
            request = json.loads(self.rfile.read(length) or b"{}")
            try:
                response = handle_chat_completion(
                    request, corpus, client, provider,
                    k=config.k, cheap_model=config.models.cheap, ledger=ledger,
                )
            except Exception as exc:  # a bad request shouldn't kill the process
                self.send_error(500, str(exc))
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            chunk = {"choices": [{"delta": response["choices"][0]["message"]}]}
            self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
            self.wfile.write(b"data: [DONE]\n\n")

        def log_message(self, fmt: str, *args: Any) -> None:  # no message bodies logged
            pass

    return Handler


def serve(config_path: str, host: str = "127.0.0.1", port: int = 8080, log_conversations: bool = False) -> None:
    """Build the warm corpus from acri.yaml, then block serving requests.
    Binds localhost by default -- a resolver holding provider credentials on
    0.0.0.0 is a credential proxy for the whole network."""
    config = from_yaml(config_path)
    missing = missing_env_vars(config)
    if missing:
        raise RuntimeError(f"missing credentials: {', '.join(missing)} -- run `acri check {config_path}`")

    tools = asyncio.run(connect_all(config.mcp)) + resolve_builtin(config.builtin)
    corpus = index(tools)
    write_corpus_snapshot(corpus)  # lets studio show unresolved tools too, without connecting itself
    provider = provider_for(config.models.default or "gemini")
    client = _client_for(provider)
    ledger = default_ledger() if log_conversations else RedactingLedger(default_ledger())

    handler = _make_handler(config, corpus, client, provider, ledger)
    httpd = ThreadingHTTPServer((host, port), handler)
    print(f"acri up: {len(corpus)} tools, {provider}, http://{host}:{port}/v1/chat/completions")
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
