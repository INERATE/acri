"""port — provider adapters. Accept a resolved toolset, call the provider, normalize the reply.

acri never imports `openai` or `google-genai`. `client` is duck-typed: pass
whatever SDK client you already constructed. This keeps acri dependency-free
and makes provider calls trivial to fake in tests — see tests/test_ports.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .compass import Resolved
from .schemas import to_openai_tools


@dataclass(frozen=True)
class GenerationResult:
    """A normalized reply: text, any tool calls the model asked for, and the raw response."""

    text: str | None
    tool_calls: list[dict[str, Any]]
    raw: Any


def openai_compatible(client: Any, prompt: str, resolved: list[Resolved], model: str = "gpt-4o-mini") -> GenerationResult:
    """Call any OpenAI-compatible client — OpenAI, vLLM, Ollama, DeepSeek, Together."""
    tools = to_openai_tools(resolved)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        tools=tools or None,
    )
    message = response.choices[0].message
    calls = [{"name": c.function.name, "arguments": c.function.arguments} for c in (message.tool_calls or [])]
    return GenerationResult(text=message.content, tool_calls=calls, raw=response)


def cached_call(call: Any, cache: dict[Any, GenerationResult] | None, key: Any, *args: Any, **kwargs: Any) -> GenerationResult:
    """Run `call(*args, **kwargs)`, or return the prior result if `key` is already in `cache`.

    docs/decisions.md #8c: exact-match only, no similarity. `cache` is a plain dict the
    caller owns -- pass None (the default via run()) to disable it entirely.
    """
    if cache is not None and key in cache:
        return cache[key]
    result = call(*args, **kwargs)
    if cache is not None:
        cache[key] = result
    return result


