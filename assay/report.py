"""report — print the accuracy.py results table. Split out purely to stay under the file cap."""
from __future__ import annotations

import statistics


def print_accuracy_report(provider: str, k: int, n: int, n_tools: int, hits: dict, latency_ms: dict) -> None:
    print(f"provider={provider} k={k}  n={n} queries, {n_tools} tools in corpus\n")
    print(f"{'arm':>6} {'accuracy':>12} {'median ms':>10} {'p90 ms':>8}")
    for arm in ("naive", "acri"):
        lat = sorted(latency_ms[arm])
        p90 = lat[int(len(lat) * 0.9)] if lat else float("nan")
        print(f"{arm:>6} {hits[arm]}/{n} ({100 * hits[arm] / n:.0f}%){'':>1} "
              f"{statistics.median(lat):>10.0f} {p90:>8.0f}")
    print("\nLatency here is per-call, single-shot (no repeated turns in one task), so it does "
          "not reflect the resolve-once-per-task caching acri.run() is designed around -- see "
          "docs/decisions.md #4.1. It answers a narrower, still-real question: does sending "
          "the full tool schema block cost time on a cold, uncached call.")
