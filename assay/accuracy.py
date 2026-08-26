"""accuracy — does the model pick the right tool with acri vs. with everything?

Needs a live API key, costs real money, and is not run in CI. Two arms:

    naive — every tool in the corpus is shown to the model on every query.
    acri  — only compass's top-k are shown.

This replaces an earlier "three-arm: naive, cache-enabled, acri" plan.
That was wrong: prompt caching changes what a call costs, not what tools
the model sees, so a cache-enabled arm cannot score differently from naive
on *accuracy* — it's a cost question, and docs/decisions.md already answers
the cost question with arithmetic, not a benchmark.

Run with a key set:
    OPENAI_API_KEY=... python -m assay.accuracy --provider openai
    GEMINI_API_KEY=... python -m assay.accuracy --provider gemini
"""
from __future__ import annotations

import argparse
import os

from acri.compass import Resolved, resolve
from acri.corpus import index

from .fixtures import load_gold, load_tools


def _openai_client():
    import openai

    return openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def _gemini_client():
    from google import genai

    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


_CLIENTS = {"openai": _openai_client, "gemini": _gemini_client}


def run(provider: str, k: int = 5) -> None:
    from acri.port import gemini, openai_compatible

    call = {"openai": openai_compatible, "gemini": gemini}[provider]
    client = _CLIENTS[provider]()

    tools = load_tools()
    corpus = index(tools)
    everything = [Resolved(tool=t, score=1.0) for t in tools]
    gold = [g for g in load_gold() if g.tool is not None]

    hits = {"naive": 0, "acri": 0}
    for g in gold:
        naive_reply = call(client, g.query, everything)
        acri_reply = call(client, g.query, resolve(g.query, corpus, k=k))
        if naive_reply.tool_calls and naive_reply.tool_calls[0]["name"] == g.tool:
            hits["naive"] += 1
        if acri_reply.tool_calls and acri_reply.tool_calls[0]["name"] == g.tool:
            hits["acri"] += 1

    print(f"provider={provider} k={k}  n={len(gold)} queries, {len(tools)} tools in corpus\n")
    for arm, n_hits in hits.items():
        print(f"{arm:>6}: {n_hits}/{len(gold)} ({100 * n_hits / len(gold):.0f}%)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare naive vs. acri tool-selection accuracy against a live model.")
    parser.add_argument("--provider", choices=sorted(_CLIENTS), required=True)
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()
    run(args.provider, args.k)


if __name__ == "__main__":
    main()
