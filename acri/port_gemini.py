"""port_gemini — the Gemini native adapter. One file per native provider (file-size
cap, and it stops this fight recurring every time a new provider joins).
"""
from __future__ import annotations

from typing import Any

from .compass import Resolved
from .port import GenerationResult
from .schemas import to_gemini_tools


def gemini(client: Any, prompt: str, resolved: list[Resolved], model: str = "gemini-2.5-flash") -> GenerationResult:
    """Call a Gemini client (the `google-genai` SDK shape). Also serves Vertex AI --
    same wire format, only the client's auth differs, entirely in clients.py."""
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
