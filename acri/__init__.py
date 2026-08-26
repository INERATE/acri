"""acri — a client-side capability resolver. `import acri` is the whole product.

`run()` is the one function that touches every module: corpus's index,
compass's ranking, port's provider call, and ledger's trace. Integration
tests call this, not a hand-wired re-implementation of the pipeline.

Named `__init__.py`, not `kernel.py`: docs/architecture.md #5 retired
kernel/runtime/OS vocabulary for this project on purpose. The entry point
doesn't get to bring it back through the filename.
"""
from __future__ import annotations

import time
from typing import Any

from .adapters import from_callables, from_mcp_tools
from .compass import Resolved
from .compass import resolve as _compass_resolve
from .corpus import Corpus, Tool, index
from .ledger import Entry, Ledger
from .port import GenerationResult, gemini, openai_compatible

__all__ = [
    "Tool", "Corpus", "index", "from_callables", "from_mcp_tools",
    "Resolved", "resolve",
    "GenerationResult", "gemini", "openai_compatible",
    "Entry", "Ledger",
    "run",
]

_PROVIDERS = {"openai": openai_compatible, "gemini": gemini}


def resolve(query: str, corpus: Corpus, k: int = 5) -> list[Resolved]:
    """Rank `corpus` against `query`, return the top k. See compass.resolve for the algorithm."""
    return _compass_resolve(query, corpus, k)


def run(
    query: str,
    corpus: Corpus,
    client: Any,
    provider: str = "openai",
    *,
    k: int = 5,
    model: str | None = None,
    ledger: Ledger | None = None,
) -> GenerationResult:
    """Resolve tools for `query`, call `provider` with them, log the trace if a ledger is given."""
    call = _PROVIDERS.get(provider)
    if call is None:
        raise ValueError(f"unknown provider: {provider!r} (expected one of {sorted(_PROVIDERS)})")
    start = time.time()
    resolved = _compass_resolve(query, corpus, k)
    kwargs = {"model": model} if model else {}
    result = call(client, query, resolved, **kwargs)
    if ledger is not None:
        selected = [c["name"] for c in result.tool_calls]
        ledger.record(query, resolved, selected, (time.time() - start) * 1000)
    return result
