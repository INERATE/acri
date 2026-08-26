"""diagnose -- decompose acri accuracy failures: resolver miss vs. model miss.

Needs a live API key. Two different failure modes, two different owners:
compass either offers the gold tool or it doesn't (recall); given that it
did, the model either picks it or picks something else (the model's job,
per docs/architecture.md #4.2's division of labor -- acri does not own this).
"""
from __future__ import annotations

import argparse

from acri.compass import resolve
from acri.corpus import index

from .clients import CLIENTS
from .fixtures import load_gold, load_tools


def run(provider: str, k: int = 5) -> None:
    from acri.port import gemini, openai_compatible

    call = {"openai": openai_compatible, "gemini": gemini, "vertex": gemini}[provider]
    client = CLIENTS[provider]()

    corpus = index(load_tools())
    gold = [g for g in load_gold() if g.tool is not None]

    resolver_miss, model_miss, hit = [], [], 0
    for g in gold:
        resolved = resolve(g.query, corpus, k=k)
        offered = {r.tool.name for r in resolved}
        if g.tool not in offered:
            resolver_miss.append(g)
            continue
        reply = call(client, g.query, resolved)
        picked = reply.tool_calls[0]["name"] if reply.tool_calls else None
        if picked == g.tool:
            hit += 1
        else:
            model_miss.append((g, picked, sorted(offered)))

    n = len(gold)
    print(f"n={n}  hit={hit} ({100 * hit / n:.0f}%)  resolver_miss={len(resolver_miss)}  model_miss={len(model_miss)}\n")

    print("--- resolver never offered the gold tool (compass's job) ---")
    for g in resolver_miss:
        print(f"  {g.query!r} -> wanted {g.tool}")

    print("\n--- gold tool WAS offered, model picked something else (model's job) ---")
    for g, picked, offered in model_miss:
        print(f"  {g.query!r}\n    wanted: {g.tool}  picked: {picked}\n    offered: {offered}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Decompose acri accuracy into resolver-miss vs. model-miss.")
    parser.add_argument("--provider", choices=sorted(CLIENTS), required=True)
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()
    run(args.provider, args.k)


if __name__ == "__main__":
    main()
