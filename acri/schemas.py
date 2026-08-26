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
    """Shape resolved tools into a Gemini `function_declarations` block."""
    return [{"name": r.tool.name, "description": r.tool.description, "parameters": r.tool.parameters} for r in resolved]
