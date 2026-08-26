"""recall — does the correct tool appear in compass's top k? No API key needed.

This is the metric docs/decisions.md says matters most: recall@k, not
resolver latency. Run: `python -m assay.recall` from the repo root.
"""
from __future__ import annotations

from acri.compass import resolve
from acri.corpus import index

from .fixtures import load_gold, load_tools


def recall_at_k(k: int) -> tuple[int, int]:
    """Return (hits, answerable) for this k, over every gold query with a correct tool."""
    corpus = index(load_tools())
    hits = 0
    answerable = 0
    for g in load_gold():
        if g.tool is None:
            continue
        answerable += 1
        names = {r.tool.name for r in resolve(g.query, corpus, k=k)}
        if g.tool in names:
            hits += 1
    return hits, answerable


def false_positive_rate_on_unanswerable() -> tuple[int, int]:
    """Of queries with NO correct tool in the corpus, how often does resolve() return nothing?"""
    corpus = index(load_tools())
    unanswerable = [g for g in load_gold() if g.tool is None]
    silent = sum(1 for g in unanswerable if not resolve(g.query, corpus, k=5))
    return silent, len(unanswerable)


def main() -> None:
    n_tools = len(load_tools())
    print(f"corpus: {n_tools} tools\n")
    print(f"{'k':>3} {'recall@k':>10} {'reduction vs all':>18}")
    for k in (1, 3, 5, 10):
        hits, total = recall_at_k(k)
        print(f"{k:>3} {hits}/{total} ({100*hits/total:.0f}%){' ':>3} {n_tools}->{k} tools ({100*(1 - k/n_tools):.0f}% fewer)")
    silent, total = false_positive_rate_on_unanswerable()
    print(f"\nunanswerable queries correctly returning nothing: {silent}/{total}")


if __name__ == "__main__":
    main()
