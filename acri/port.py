"""port — provider adapters. Accept a resolved toolset, call the provider, normalize the reply.

acri never imports `openai` or `google-genai`. `client` is duck-typed: pass
whatever SDK client you already constructed. This keeps acri dependency-free
and makes provider calls trivial to fake in tests — see tests/test_ports.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .compass import Resolved
from .schemas import to_gemini_tools, to_openai_tools


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


def gemini(client: Any, prompt: str, resolved: list[Resolved], model: str = "gemini-2.5-flash") -> GenerationResult:
    """Call a Gemini client (the `google-genai` SDK shape)."""
    tools = to_gemini_tools(resolved)
    config = {"tools": [{"function_declarations": tools}]} if tools else {}
    response = client.models.generate_content(model=model, contents=prompt, config=config)
    # candidate.content (and .parts) can be None -- a safety block, a
    # recitation block, or MAX_TOKENS hit before any content -- all real,
    # not hypothetical: response.candidates[0].finish_reason has the reason.
    content = response.candidates[0].content
    text = None
    calls = []
    for part in (content.parts if content else None) or []:
        if getattr(part, "text", None):
            text = part.text
        fc = getattr(part, "function_call", None)
        if fc:
            calls.append({"name": fc.name, "arguments": dict(fc.args)})
    return GenerationResult(text=text, tool_calls=calls, raw=response)
