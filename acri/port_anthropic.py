"""port_anthropic — the direct Claude API adapter (console.anthropic.com, not
Bedrock/Vertex -- those are separate wire formats, port_bedrock.py/port_gemini.py).
"""
from __future__ import annotations

from typing import Any

from .compass import Resolved
from .port import GenerationResult
from .schemas import to_anthropic_tools


def anthropic(client: Any, prompt: str, resolved: list[Resolved], model: str = "claude-sonnet-4-6", max_tokens: int = 1024) -> GenerationResult:
    """Call a direct Anthropic Messages API client (the `anthropic` SDK shape).
    max_tokens is required by this API, unlike every other provider here --
    1024 is a plain default, pass a larger one for a longer expected reply."""
    tools = to_anthropic_tools(resolved)
    response = client.messages.create(
        model=model, max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        tools=tools or [],
    )
    # Same defensive shape as gemini()/bedrock(): stop_reason can be
    # "max_tokens" or a refusal before any tool_use block appears.
    text = None
    calls = []
    for block in response.content or []:
        if getattr(block, "type", None) == "text":
            text = block.text
        elif getattr(block, "type", None) == "tool_use":
            calls.append({"name": block.name, "arguments": block.input})
    return GenerationResult(text=text, tool_calls=calls, raw=response)
