"""scale — does recall and latency hold up at ~5x corpus size? No API key needed.

fixtures_500.json = the same 100 tools + 52 gold queries as fixtures.json, plus
~400 new tools across ~40 new domains -- corpus size is the only variable that
changes, so these numbers are directly comparable to recall.py/latency.py's
100-tool numbers. Not a replacement for those -- see README's First numbers.
Run: `python -m assay.scale` from the repo root.
"""
from __future__ import annotations

import statistics
import time
from pathlib import Path

from acri.compass import resolve
from acri.corpus import index

from .fixtures import load_gold, load_tools

_SCALE = Path(__file__).parent / "fixtures_500.json"


def _recall_at_k(corpus, gold, k: int) -> tuple[int, int]:
    hits = answerable = 0
    for g in gold:
        if g.tool is None:
            continue
        answerable += 1
        if g.tool in {r.tool.name for r in resolve(g.query, corpus, k=k)}:
            hits += 1
    return hits, answerable


def _latency_ms(corpus, queries: list[str]) -> tuple[float, float]:
    resolve(queries[0], corpus, k=5)  # warm-up call discarded, same as latency.py
    samples = [
        (time.perf_counter(), resolve(q, corpus, k=5), time.perf_counter())
        for _ in range(20) for q in queries
    ]
    ms = sorted((end - start) * 1000 for start, _, end in samples)
    return statistics.median(ms), ms[int(len(ms) * 0.95)]


def main() -> None:
    corpus = index(load_tools(_SCALE))
    gold = load_gold(_SCALE)
    queries = [g.query for g in gold]

    print(f"corpus: {len(corpus)} tools (vs. 100 in the published First numbers)\n")
    print(f"{'k':>3} {'recall@k':>10}")
    for k in (1, 3, 5, 10):
        hits, total = _recall_at_k(corpus, gold, k)
        print(f"{k:>3} {hits}/{total} ({100 * hits / total:.0f}%)")

    unanswerable = [g for g in gold if g.tool is None]
    silent = sum(1 for g in unanswerable if not resolve(g.query, corpus, k=5))
    print(f"\nunanswerable queries correctly returning nothing: {silent}/{len(unanswerable)}")

    p50, p95 = _latency_ms(corpus, queries)
    print(f"latency: p50 {p50:.3f} ms, p95 {p95:.3f} ms ({len(queries) * 20} resolve() calls)")


if __name__ == "__main__":
    main()
