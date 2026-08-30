"""daemon — the request handler `acri up` will eventually serve over HTTP.

No socket here, on purpose: this is the thin OpenAI-shaped layer over
acri.run(), kept separately testable so "the daemon is a thin wrapper over
the library, never a superset" (docs/decisions.md) is a test, not just a
sentence. Wiring this into a real listening process is v1.0's gated part.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import run
from ._openai_wire import extract_text
from .corpus import Corpus
from .ledger import Ledger
from .port import GenerationResult

DEFAULT_LEDGER_PATH = Path(".acri/ledger.jsonl")


def default_ledger(path: Path | str = DEFAULT_LEDGER_PATH) -> Ledger:
    """A Ledger backed by `.acri/ledger.jsonl` (docs/decisions.md), creating the
    directory if it doesn't exist yet."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return Ledger(path)


class RedactingLedger:
    """Wraps a real Ledger, dropping the query text before it's recorded.

    docs/decisions.md: "ledger records decisions, scores, and token counts.
    Conversation content is opt-in." -- `acri up`'s default. Duck-typed to
    Ledger.record's signature, nothing else; `run()` never checks the type.
    """

    def __init__(self, ledger: Ledger) -> None:
        self._ledger = ledger

    def record(self, query: str, offered: Any, selected: list[str], latency_ms: float, cost_usd: float | None = None) -> Any:
        return self._ledger.record("<redacted>", offered, selected, latency_ms, cost_usd)


def handle_chat_completion(
    request: dict[str, Any],
    corpus: Corpus,
    client: Any,
    provider: str = "openai",
    *,
    k: int = 5,
    cheap_model: str | None = None,
    ledger: Ledger | None = None,
    cache: dict[Any, GenerationResult] | None = None,
) -> dict[str, Any]:
    """Handle one OpenAI-shaped `/v1/chat/completions` request via acri.run() --
    not a reimplementation of resolve+call.

    Single-turn only: the last message's content is the query -- a plain string, or an
    OpenAI-shaped multimodal list (image_url/input_audio parts), passed through as
    run()'s `prompt` unchanged. `acri/server.py` wraps this in SSE at the wire level;
    multi-turn history and true upstream streaming are still open.
    """
    messages = request.get("messages") or []
    content = messages[-1]["content"] if messages else ""
    result = run(
        extract_text(content), corpus, client, provider,
        k=k, model=request.get("model"), cheap_model=cheap_model,
        ledger=ledger, cache=cache, prompt=None if isinstance(content, str) else content,
    )
    message: dict[str, Any] = {"role": "assistant", "content": result.text}
    if result.tool_calls:
        message["tool_calls"] = [
            {"id": f"call_{i}", "type": "function", "function": tc}
            for i, tc in enumerate(result.tool_calls)
        ]
    return {"choices": [{"message": message}]}
