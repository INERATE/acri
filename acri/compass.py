"""compass — the resolver. Given a query, returns the k tools that matter.

This is the product. It performs no language understanding — BM25 scores
query terms against tool text, weighting terms that are rare in the corpus.
That's deliberate: understanding is the model's job and costs a model call.
compass only does recall (narrow N tools to k candidates); the model still
does precision (pick one, write its arguments). See docs/decisions.md.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ._text import tokenize as _tokenize
from .corpus import Corpus, Tool

_K1 = 1.5
_B = 0.75

# Query-side synonym expansion: words a user types that never literally
# appear in any tool description -- BM25 has no stemming or semantic
# understanding, so "rain" and "weather" are unrelated tokens to it
# otherwise. Applied to the query only, never the corpus: expanding doc
# text here would let a tool's description quietly start matching queries
# for a synonym it never claimed, and would shift df/idf for every other
# tool too. Every entry below traces to a real recall@5 miss, not a guess
# -- see assay/diagnose.py.
_ALIASES: dict[str, tuple[str, ...]] = {
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


def _expand(tokens: list[str]) -> list[str]:
    expanded = list(tokens)
    for tok in tokens:
        expanded.extend(_ALIASES.get(tok, ()))
    return expanded


@dataclass(frozen=True)
class Resolved:
    """One ranked tool and acri's confidence in it.

    `score` is relative to the best match for this query (1.0 = best), not a
    calibrated probability — a 0.9 does not mean "90% sure".
    """

    tool: Tool
    score: float


def _idf(df: int, n_docs: int) -> float:
    return math.log(1 + (n_docs - df + 0.5) / (df + 0.5))


def _bm25(query_tokens: list[str], corpus: Corpus, doc_idx: int) -> float:
    doc_len = len(corpus.doc_tokens[doc_idx])
    freqs = corpus.doc_freqs[doc_idx]
    n_docs = len(corpus.tools)
    score = 0.0
    for tok in query_tokens:
        f = freqs.get(tok)
        if not f:
            continue
        idf = _idf(corpus.df.get(tok, 0), n_docs)
        denom = f + _K1 * (1 - _B + _B * doc_len / corpus.avgdl)
        score += idf * (f * (_K1 + 1)) / denom
    return score


def resolve(query: str, corpus: Corpus, k: int = 5) -> list[Resolved]:
    """Rank every tool in `corpus` against `query`, return the top k.

    Tools that score zero (no shared term with the query) are dropped rather
    than padded in — an empty result means "nothing in this corpus matches",
    which the caller should handle via `port`'s no-tools path, not treat as
    an error.
    """
    if len(corpus) == 0:
        return []
    query_tokens = _expand(_tokenize(query))
    raw = [_bm25(query_tokens, corpus, i) for i in range(len(corpus))]
    top = max(raw, default=0.0)
    if top <= 0.0:
        return []
    scored = [Resolved(tool=corpus.tools[i], score=raw[i] / top) for i in range(len(corpus)) if raw[i] > 0.0]
    scored.sort(key=lambda r: r.score, reverse=True)
    return scored[:k]
