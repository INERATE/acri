"""gate — the necessity check, advisory only. docs/architecture.md #4.2, #4.3.

Pipeline is retrieve -> score -> gate: a threshold on the raw BM25 score
compass already computes, not a second classifier -- a tool registered a
second ago still works, because the signal comes from the live corpus, not
from training data (#4.2).

Uncalibrated on purpose: no default threshold ships as "the right one" --
that needs real ledger data this project doesn't have yet (docs/decisions.md).
The asymmetry that shapes the API: a false "offer tools" costs a few tokens
and shows up in the trace; a false "don't" is a silent, unlogged wrong
answer (#4.3). So gate only ever advises skipping the tool block for this
turn -- it has no way to filter or block a tool call the model already
returned, because nothing downstream calls it a second time.
"""
from __future__ import annotations

from ._synonyms import expand as _expand
from ._text import tokenize as _tokenize
from .compass import bm25
from .corpus import Corpus


def raw_top_score(query: str, corpus: Corpus) -> float:
    """The best match's un-normalized BM25 score. Unlike compass.Resolved.score
    (always 1.0 for whichever tool wins, by construction), this can tell a
    strong match apart from a weak coincidental one. 0.0 for an empty corpus
    or no shared term with any tool -- same case compass.resolve() treats as
    an empty result.
    """
    if len(corpus) == 0:
        return 0.0
    tokens = _expand(_tokenize(query))
    return max((bm25(tokens, corpus, i) for i in range(len(corpus))), default=0.0)


def should_offer_tools(query: str, corpus: Corpus, threshold: float) -> bool:
    """True unless the best match is weaker than `threshold`. The caller picks
    the threshold -- pick it too low and this never advises skipping anything
    (safe: matches resolve()'s own behavior); too high and real turns get
    skipped (the dangerous direction, see the module docstring)."""
    return raw_top_score(query, corpus) >= threshold
