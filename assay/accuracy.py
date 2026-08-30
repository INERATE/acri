"""accuracy — does the model pick the right tool with acri vs. with everything?

Needs a live API key, costs real money, and is not run in CI. Two arms:

    naive — every tool in the corpus is shown to the model on every query.
    acri  — only compass's top-k are shown.

This replaces an earlier "three-arm: naive, cache-enabled, acri" plan.
That was wrong: prompt caching changes what a call costs, not what tools
the model sees, so a cache-enabled arm cannot score differently from naive
on *accuracy* — it's a cost question, and docs/decisions.md already answers
the cost question with arithmetic, not a benchmark.

Run with a key set (every provider's env vars and an example: README.md):
    GEMINI_API_KEY=... python -m assay.accuracy --provider gemini

Every provider dispatches through acri.providers.PROVIDERS -- the same table
`acri up` uses, not a second copy. A provider with no safe default model
(cloudflare, openrouter, nvidia, grok, ollama, vllm, lmstudio -- acri.providers
has no single "the" model for any of them) needs --model.
"""
from __future__ import annotations

import argparse
import time

from acri.compass import Resolved, resolve
from acri.corpus import index
from acri.providers import PROVIDERS

from .clients import CLIENTS
from .fixtures import load_gold, load_tools
from .report import print_accuracy_report

_NO_DEFAULT_MODEL = {"cloudflare", "openrouter", "nvidia", "grok", "ollama", "vllm", "lmstudio", "azure-grok"}


def run(provider: str, k: int = 5, model: str | None = None) -> None:
    call = PROVIDERS[provider]
    if provider in _NO_DEFAULT_MODEL and not model:
        raise SystemExit(f"{provider} needs --model -- it has no single default (e.g. --model @cf/meta/llama-3.3-70b-instruct)")
    call_kwargs = {"model": model} if model else {}
    client = CLIENTS[provider]()

    tools = load_tools()
    corpus = index(tools)
    everything = [Resolved(tool=t, score=1.0) for t in tools]
    gold = [g for g in load_gold() if g.tool is not None]

    hits = {"naive": 0, "acri": 0}
    latency_ms = {"naive": [], "acri": []}
    for g in gold:
        start = time.perf_counter()
        naive_reply = call(client, g.query, everything, **call_kwargs)
        latency_ms["naive"].append((time.perf_counter() - start) * 1000)

        start = time.perf_counter()
        acri_reply = call(client, g.query, resolve(g.query, corpus, k=k), **call_kwargs)
        latency_ms["acri"].append((time.perf_counter() - start) * 1000)

        if naive_reply.tool_calls and naive_reply.tool_calls[0]["name"] == g.tool:
            hits["naive"] += 1
        if acri_reply.tool_calls and acri_reply.tool_calls[0]["name"] == g.tool:
            hits["acri"] += 1

    print_accuracy_report(provider, k, len(gold), len(tools), hits, latency_ms)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare naive vs. acri tool-selection accuracy against a live model.")
    parser.add_argument("--provider", choices=sorted(CLIENTS), required=True)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--model", default=None, help="override the provider's default model")
    args = parser.parse_args()
    run(args.provider, args.k, args.model)


if __name__ == "__main__":
    main()
