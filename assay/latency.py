"""latency — how long compass.resolve() actually takes. No API key needed.

This is reported, never headlined: docs/decisions.md is explicit that
recall is the metric that matters and latency is second, because a resolver
runs against a network call that dominates it. This script exists so that
claim has a number behind it instead of an assumption.
Run: `python -m assay.latency` from the repo root.
"""
from __future__ import annotations

import statistics
import time

from acri.compass import resolve
from acri.corpus import index

from .fixtures import load_gold, load_tools


def main() -> None:
    corpus = index(load_tools())
    queries = [g.query for g in load_gold()]

    # Warm up: the first call pays for CPython's import/bytecode caching, not
    # the algorithm. Discard it like any other microbenchmark would.
    resolve(queries[0], corpus, k=5)

    samples_ms = []
    for _ in range(20):
        for q in queries:
            start = time.perf_counter()
            resolve(q, corpus, k=5)
            samples_ms.append((time.perf_counter() - start) * 1000)

    samples_ms.sort()
    p50 = statistics.median(samples_ms)
    p95 = samples_ms[int(len(samples_ms) * 0.95)]
    print(f"corpus: {len(corpus)} tools, {len(samples_ms)} resolve() calls")
    print(f"p50: {p50:.3f} ms   p95: {p95:.3f} ms   max: {max(samples_ms):.3f} ms")


if __name__ == "__main__":
    main()
