"""adapters — turn external tool descriptions into `corpus.Tool`."""
from __future__ import annotations

import inspect
from typing import Any, Callable

from .corpus import Tool

_TYPE_MAP = {str: "string", int: "integer", float: "number", bool: "boolean"}


def from_mcp_tools(mcp_tools: list[dict[str, Any]]) -> list[Tool]:
    """Adapt an MCP `tools/list` response into Tools. Feed the result to `index()`."""
    return [
        Tool(
            name=t["name"],
            description=t.get("description", ""),
            parameters=t.get("inputSchema", {"type": "object", "properties": {}}),
        )
        for t in mcp_tools
    ]


def _schema_from_callable(f: Callable[..., Any]) -> dict[str, Any]:
    sig = inspect.signature(f)
    props: dict[str, Any] = {}
    required: list[str] = []
    for name, param in sig.parameters.items():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        props[name] = {"type": _TYPE_MAP.get(param.annotation, "string")}
        if param.default is inspect.Parameter.empty:
            required.append(name)
    schema: dict[str, Any] = {"type": "object", "properties": props}
    if required:
        schema["required"] = required
    return schema


def from_callables(funcs: list[Callable[..., Any]]) -> list[Tool]:
    """Adapt plain Python functions into Tools, deriving each schema from its signature."""
    return [
        Tool(
            name=f.__name__,
            description=(f.__doc__ or "").strip(),
            parameters=_schema_from_callable(f),
            handler=f,
        )
        for f in funcs
    ]
