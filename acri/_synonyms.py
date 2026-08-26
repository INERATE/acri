"""_synonyms — query-side alias expansion for compass. Not corpus-facing.

Words a user types that never literally appear in any tool description --
BM25 has no stemming or semantic understanding, so "rain" and "weather" are
unrelated tokens to it otherwise. Applied to the query only, never the
corpus: expanding doc text here would let a tool's description quietly
start matching queries for a synonym it never claimed, and would shift
df/idf for every other tool too. Every entry traces to a real recall@5
miss, not a guess -- see assay/diagnose.py.
"""
from __future__ import annotations

ALIASES: dict[str, tuple[str, ...]] = {
    "pr": ("pull", "request"),
    "meeting": ("event",),
    "rain": ("weather",),
    "raining": ("weather",),
    "storm": ("weather",),
    "warning": ("alerts",),
    "warnings": ("alerts",),
    "text": ("sms", "message"),
    "sharpen": ("upscale", "resolution"),
    "money": ("refund", "charge"),
}


def expand(tokens: list[str]) -> list[str]:
    expanded = list(tokens)
    for tok in tokens:
        expanded.extend(ALIASES.get(tok, ()))
    return expanded
