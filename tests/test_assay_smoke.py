"""Guards the numbers in README.md against silent regressions.

Not pinned to exact percentages — float/version drift would make that
flaky. Pinned to the invariants a real regression would break: recall rises
with k, stays well above chance, and resolve() stays fast.
"""
from assay.fixtures import load_gold, load_tools
from assay.recall import false_positive_rate_on_unanswerable, recall_at_k
from acri.compass import resolve
from acri.corpus import index


def test_recall_improves_with_k_and_beats_chance():
    by_k = {k: recall_at_k(k) for k in (1, 3, 5, 10)}
    rates = {k: hits / total for k, (hits, total) in by_k.items()}
    assert rates[1] <= rates[3] <= rates[5] <= rates[10]
    assert rates[5] > 0.5  # far above 5/100 chance for a 100-tool corpus


def test_unanswerable_queries_do_not_force_a_match():
    silent, total = false_positive_rate_on_unanswerable()
    assert silent == total


def test_resolve_is_fast_at_this_scale():
    import time

    corpus = index(load_tools())
    query = load_gold()[0].query
    start = time.perf_counter()
    resolve(query, corpus, k=5)
    assert (time.perf_counter() - start) < 0.05  # generous; assay/latency.py has the real number
