"""port_openai_responses — the newer OpenAI Responses API shape (`input`/`output`,
not `messages`/`tool_calls`). Azure AI Foundry's `/openai/v1/responses` endpoint
speaks this, as does `api.openai.com` directly for models that support it. A
distinct wire format from `openai_compatible()`'s chat-completions shape --
tool schemas are flat (no nested `function` key) -- hence its own file.
"""
from __future__ import annotations

from typing import Any

from .compass import Resolved
from .port import GenerationResult
from .schemas import to_openai_tools


def openai_responses(client: Any, prompt: str, resolved: list[Resolved], model: str = "gpt-5-mini") -> GenerationResult:
    """Call `client.responses.create()`. Flattens `to_openai_tools()`'s nested
    `{"function": {...}}` shape, since Responses wants name/description/parameters
    directly on the tool dict."""
    flat_tools = [
        {"type": "function", "name": t["function"]["name"],
         "description": t["function"]["description"], "parameters": t["function"]["parameters"]}
        for t in to_openai_tools(resolved)
    ]
    response = client.responses.create(model=model, input=prompt, tools=flat_tools)
    text = None
    calls = []
    for item in getattr(response, "output", None) or []:
        if getattr(item, "type", None) == "function_call":
            calls.append({"name": item.name, "arguments": item.arguments})
        elif getattr(item, "type", None) == "message":
            for block in getattr(item, "content", None) or []:
                if getattr(block, "type", None) == "output_text":
                    text = block.text
    return GenerationResult(text=text, tool_calls=calls, raw=response)
