"""schemas — shape resolved tools into each provider's wire format. Pure data, no I/O."""
from __future__ import annotations

from typing import Any

from .compass import Resolved


def to_openai_tools(resolved: list[Resolved]) -> list[dict[str, Any]]:
    """Shape resolved tools into the OpenAI-compatible `tools=[...]` array."""
    return [
        {
            "type": "function",
            "function": {"name": r.tool.name, "description": r.tool.description, "parameters": r.tool.parameters},
        }
        for r in resolved
    ]


def to_gemini_tools(resolved: list[Resolved]) -> list[dict[str, Any]]:
    """Shape resolved tools into a Gemini `function_declarations` block.

    Strips `$schema`: real MCP servers commonly self-declare their JSON Schema
    dialect there (e.g. @modelcontextprotocol/server-filesystem), and Gemini's
    function-calling schema -- unlike OpenAI's -- rejects it as an unrecognized
    field. Found live (acri/server.py smoke test against a real MCP server), not
    guessed; every synthetic fixture in this repo lacked the key, so nothing else
    could have caught it.
    """
    return [
        {"name": r.tool.name, "description": r.tool.description,
         "parameters": {k: v for k, v in r.tool.parameters.items() if k != "$schema"}}
        for r in resolved
    ]
