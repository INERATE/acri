"""router — picks a model tier once, before generation. docs/decisions.md #1, architecture.md #4.4.

Not a classifier: whether a task is stateless and prefix-free (classification,
extraction, summarizing a tool result -- architecture.md #4.4) is the caller's
judgment, not something acri infers from query text. A learned dispatcher was
cut on purpose -- docs/decisions.md #11. acri's only job is making the tier
choice happen once, before any provider call, never mid-stream.
"""
from __future__ import annotations


def route(model: str | None, cheap_model: str | None) -> str | None:
    """Use `cheap_model` when the caller supplied one for this call, else `model`.

    Passing `cheap_model` *is* the eligibility judgment -- there is no separate
    flag that could disagree with it. On a cheap-tier failure, call again with
    `cheap_model=None` and the same unmodified `query`: the strong-tier call gets
    its own cache key (model is part of it -- see port.cached_call), so nothing
    from the failed attempt leaks in, and nothing needs to be re-typed.
    """
    return cheap_model or model
