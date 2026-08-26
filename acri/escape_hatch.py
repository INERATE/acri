"""escape_hatch — find_more_tools, the recovery path architecture.md #4.1 names.

`compass.resolve()` picks k tools once per task and that resolution is never
rewritten (see compass.py, decisions.md #4.1: rewriting a sent prefix costs
more than doing nothing). But a bad initial resolution still has to be
recoverable, so `compass` "always includes a find_more_tools capability" --
this is that capability, kept out of compass.py so resolve()'s own contract
(pure ranking, nothing appended) stays untouched and every recall@k number
in assay/ stays valid.

`acri.run()` appends FIND_MORE_TOOLS to what's actually sent to the provider,
not to the ledger's `offered` -- the ledger records what compass resolved,
not the constant scaffolding wrapped around it. Calling it re-searches the
full corpus; acri never auto-executes it, same as any other Tool.handler.
"""
from __future__ import annotations

from .compass import resolve
from .corpus import Corpus, Tool

FIND_MORE_TOOLS = Tool(
    name="find_more_tools",
    description="Search for tools beyond the ones already offered, when none of them fit this task.",
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string", "description": "what capability you need"}},
        "required": ["query"],
    },
)


def find_more_tools(query: str, corpus: Corpus, exclude: list[str] | None = None, k: int = 5) -> list[dict[str, str]]:
    """Re-run resolution against the full corpus, skipping names already offered.
    The caller executes this when the model calls `find_more_tools` and appends
    the result as a normal tool result -- an append, never a rewrite."""
    exclude = set(exclude or ())
    found = resolve(query, corpus, k=k + len(exclude))
    return [{"name": r.tool.name, "description": r.tool.description} for r in found if r.tool.name not in exclude][:k]
