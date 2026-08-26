# acri

**A**gent **C**apability **R**esolution **I**nterface

> DNS resolves a name to an address.
> **acri resolves an intent to the right tools.**

You don't hand a browser all 300 million domains. You shouldn't hand a model all 300 tools.

---

## The problem

Tool selection degrades as your toolset grows. Anthropic's own documentation puts the
cliff at **30–50 tools**: past that, the model starts picking the wrong one.

The fix is to stop sending every schema on every request, and send only the few that
matter for the current turn. Anthropic ships this as
[tool search](https://docs.claude.com/en/docs/agents-and-tools/tool-use/tool-search-tool).
OpenAI ships an equivalent.

**Gemini does not. Ollama does not. vLLM does not. Your 8B local model does not.**

acri is that layer, for everyone else — one import, no gateway, no daemon, no framework
to adopt.

## What acri is

A client-side, provider-agnostic capability resolver. It sits between your code and the
LLM API, and decides which tools the model gets to see this turn.

## What acri is not

- **Not an MCP replacement.** MCP defines how tools connect. acri decides which of them
  the model sees. Your existing MCP servers work unchanged.
- **Not a framework.** No orchestration, no graph, no agent loop. It is a function you
  call. Use it inside LangGraph, inside the raw SDK, or inside nothing.
- **Not a proxy or gateway.** No process to run, no port to open, no network hop added.
- **Not a model.** Bring your own key. acri never calls an LLM you didn't ask for.

## The system

```
acri
├── corpus    the capability index — MCP servers, OpenAPI, plain functions,
│             indexed into one searchable body
├── compass   the resolver — intent in, the right k tools out           ← the core
├── port      provider adapters — gemini · openai-compatible · anthropic · local
├── gate      the necessity check — does this turn need a tool at all?  (advisory)
├── press     the compactor — big payloads to short digests + a handle
├── ledger    the decision trace — what was chosen, skipped, and what it cost
└── assay     the proving ground — the only place a benchmark number may come from
```

## Status

**Pre-alpha. `corpus` + `compass` + `port` + a minimal `ledger` exist and are tested.
The first `assay/` numbers below are real and reproducible; the accuracy claim itself
still needs a live model run.**

```bash
pip install acri
```

```python
import acri

tools = acri.from_callables([get_weather, get_stock_price, merge_pull_request])
corpus = acri.index(tools)          # build once, reuse across the whole task

result = acri.run("what's the weather in Tokyo?", corpus, my_openai_client)
print(result.tool_calls)            # [{"name": "get_weather", "arguments": '{"city": "Tokyo"}'}]
```

`acri.run()` resolves, calls the provider, and — if you pass `ledger=acri.Ledger()` — records
the trace. Prefer to drive the pieces yourself? `acri.resolve(query, corpus, k=5)` returns the
ranked tools; `acri.gemini` / `acri.openai_compatible` take it from there.

Read [`docs/architecture.md`](docs/architecture.md) for the full design, the prior art it
builds on, and the claims it explicitly refuses to make. Read
[`docs/decisions.md`](docs/decisions.md) for every capability that was proposed and cut,
with the evidence that decided it.

### First numbers

Measured on a synthetic 100-tool corpus spanning 20 domains (github, postgres, stripe,
aws_ec2, jira, zendesk, ...) with realistic cross-domain confusability, and 50 hand-written
queries phrased the way someone would actually type them, not as paraphrases of the tool
descriptions. Reproduce: `pip install -e ".[dev]"` then `python -m assay.recall`. Fixtures
and script: [`assay/fixtures.json`](assay/fixtures.json), [`assay/recall.py`](assay/recall.py).

| k | recall@k | tools shown instead of 100 |
|---|----------|-----------------------------|
| 1 | 64% — [`assay/recall.py`](assay/recall.py) | 1 |
| 3 | 74% — [`assay/recall.py`](assay/recall.py) | 3 |
| 5 | 86% — [`assay/recall.py`](assay/recall.py) | 5 |
| 10 | 88% — [`assay/recall.py`](assay/recall.py) | 10 |

Both adversarial queries (no correct tool exists in the corpus) correctly resolve to
nothing, at every k.

This is recall, not the accuracy claim itself — it says the right tool is *available* to
the model in a much smaller set, not that the model picks it. That needs a live model:
[`assay/accuracy.py`](assay/accuracy.py) is built (naive vs. acri, both arms real API
calls) but not yet run — it costs money and isn't part of CI. Run it yourself:
`OPENAI_API_KEY=... python -m assay.accuracy --provider openai`.

`compass.resolve()` itself, over 1,040 calls against the same 100-tool corpus: p50 0.040ms,
p95 0.087ms ([`assay/latency.py`](assay/latency.py)). Not headlined on purpose — see
[`docs/decisions.md`](docs/decisions.md) for why resolver latency is beside the point
against a network call measured in hundreds of milliseconds.

### Roadmap

| Version | Scope | Gate to ship |
|---------|-------|--------------|
| **v0.1** | `corpus` + `compass` + `port` + minimal `ledger` | **Shipped.** `pytest` green, no native deps. |
| **v0.2** | `assay` | Recall + latency **shipped, numbers above.** Accuracy harness built, awaiting a live run. |
| **v0.3** | Pre-generation router, exact-match cache | Only what `docs/decisions.md` kept |
| **later** | `gate`, `press`, `studio` | Only if `ledger` data proves they are needed |

## The claims policy

This project makes no performance claim it cannot reproduce.

No number appears in this repository — README, docs, paper, or commit message — unless a
script in `assay/` regenerates it from a public benchmark, and the run is committed
alongside it. Estimates are labelled as estimates. Projections are labelled as
projections.

If you find a number here without its receipt, that is a bug. Please
[open an issue](../../issues/new).

## Prior art

acri stands on published work and does not pretend otherwise:

- [RAG-MCP](https://arxiv.org/abs/2505.03275) — retrieval over tool schemas to cut prompt bloat
- [When2Call](https://arxiv.org/abs/2504.18851) — when (not) to call tools
- [Anthropic tool search](https://docs.claude.com/en/docs/agents-and-tools/tool-use/tool-search-tool) and [context editing](https://docs.claude.com/en/docs/build-with-claude/context-editing) — the same idea, shipped provider-side

acri's contribution is **placement**: the same capability, client-side and
provider-agnostic, for the models that don't have it natively.

## License

MIT — see [LICENSE](LICENSE).

Built by [Piyush Sharma](https://github.com/ScienHAC) under [INERATE](https://github.com/INERATE),
alongside [Atelier](https://github.com/INERATE/atelier).
