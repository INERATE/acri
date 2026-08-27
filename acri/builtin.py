"""builtin — acri's own opt-in tool pack. docs/research/future-work-tool-pack.md.

Nothing loads unless named under acri.yaml's `tools: builtin:` -- same
"nothing runs unless configured" posture as `mcp:`. Only `press.digest` ships
for now; `sandbox.run` was considered and rejected (see the future-work doc,
open question #1) because sandbox config isn't a tool in the MCP sense.
"""
from __future__ import annotations

from typing import Any

from .corpus import Tool
from .press import press as _press


def _digest_handler(result: Any, max_chars: int = 2000, max_rows: int = 20) -> str:
    store: dict[str, Any] = {}
    return _press(result, store, max_chars=max_chars, max_rows=max_rows).digest


_REGISTRY: dict[str, Tool] = {
    "press.digest": Tool(
        name="press.digest",
        description="Compact a large tool result into a short digest, dropping nothing unrecoverably.",
        parameters={
            "type": "object",
            "properties": {
                "result": {"description": "the tool result to compact"},
                "max_chars": {"type": "integer", "default": 2000},
                "max_rows": {"type": "integer", "default": 20},
            },
            "required": ["result"],
        },
        handler=_digest_handler,
    ),
}


def resolve_builtin(names: list[str]) -> list[Tool]:
    """Look up each opted-in name. Raises ValueError on an unknown one, same
    as config.py's other validation -- fail at load time, not mid-resolve."""
    unknown = [n for n in names if n not in _REGISTRY]
    if unknown:
        raise ValueError(f"unknown builtin tool(s): {', '.join(unknown)} (known: {', '.join(_REGISTRY)})")
    return [_REGISTRY[n] for n in names]
