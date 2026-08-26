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

Recall says the right tool is *available* to the model in a much smaller set — not that
the model picks it. That's a separate, live-model question:
[`assay/accuracy.py`](assay/accuracy.py), naive (all 100 tools) vs. acri (top 5), same 50
queries, real `gemini-2.5-flash` calls, no mocking.

**A corrected result, not just a new one.** Earlier runs of this benchmark (see the commit
history on [`assay/accuracy.py`](assay/accuracy.py)) reported naive around a quarter right
and acri around half, and this README called that "acri roughly doubles accuracy." That
claim was wrong, and not because acri underperformed — the benchmark was broken in two
ways that had nothing to do with tool selection. Every one of the 100 fixture tools had an
*empty* parameter schema (no `properties` at all), and several gold queries never supplied
values a tool would need ("run *this* SQL" with no SQL attached, "text *this* customer" with
no phone number). A well-behaved model correctly declines to fabricate a ticket ID or a SQL
string and asks for it instead — and that correct, cautious behavior was being scored as a
tool-selection failure. Once both were fixed (100 tools now carry real JSON Schema
parameters; every gold query supplies a value for each of its tool's *required* fields), the
picture changed substantially:

| Arm | accuracy | median latency |
|---|---|---|
| naive (100 tools) | 72% — [`assay/accuracy.py`](assay/accuracy.py) | 1645 ms |
| acri (top 5) | 74% — [`assay/accuracy.py`](assay/accuracy.py) | 1545 ms |

**The honest reading: at 100 tools, `gemini-2.5-flash` is already good at this, and the
accuracy gap is small — a 2-point difference on 50 queries is within noise, not a doubling.**
Recall still explains the residual gap precisely: 7 of the 50 queries fail for acri because
`compass` never offers the right tool at all (real BM25 vocabulary limits — "rain" never
lexically matches "weather," "PR" never matches "pull request"; see
[`assay/diagnose.py`](assay/diagnose.py)), which caps acri below naive's ceiling by
construction. Latency again shows no meaningful difference between arms — consistent across
every run this project has done, broken-benchmark or not. This is a single run; a second
independent pass would firm up the confidence interval and is a natural next step, not yet
taken. Reproduce: `GEMINI_API_KEY=... python -m assay.accuracy --provider gemini`, or via
[Vertex AI / ADC](assay/clients.py):
`GOOGLE_APPLICATION_CREDENTIALS=... GOOGLE_CLOUD_PROJECT=... python -m assay.accuracy --provider vertex`.

What this means for the project's one claim: **recall — the context-window reduction — is
the number that survived scrutiny** (the recall@k table above, unaffected by any of the
above, since BM25 never reads a tool's parameters). The accuracy claim is real but much
more modest than first reported, and is likely to matter more as tool counts grow past what
this corpus tests — a genuinely open question, not yet measured.

**Also verified against a real MCP server, not a mock:**
[`assay/mcp_live.py`](assay/mcp_live.py) spawns the official
`@modelcontextprotocol/server-filesystem` over stdio, ingests its live `tools/list` response
through `acri.adapters.from_mcp_tools()`, resolves a query against the real 14-tool corpus,
and executes the top-ranked tool through an actual `tools/call`. `list_directory` was the
top match for "what files are in this directory" (score 1.000 of 14 candidates), and its
live result contained a marker file planted before the run specifically to prove the pipeline
is real. Run: `python -m assay.mcp_live <a-directory> "<query>"` (needs Node.js on `PATH`).

`compass.resolve()` itself, over 1,040 calls against the same 100-tool corpus: p50 0.040ms,
p95 0.087ms ([`assay/latency.py`](assay/latency.py)). Not headlined on purpose — see
[`docs/decisions.md`](docs/decisions.md) for why resolver latency is beside the point
against a network call measured in hundreds of milliseconds.

### Roadmap

| Version | Scope | Gate to ship |
|---------|-------|--------------|
| **v0.1** | `corpus` + `compass` + `port` + minimal `ledger` | **Shipped.** `pytest` green, no native deps. |
| **v0.2** | `assay` | **Shipped.** Recall, latency, and a live accuracy result, all above — the accuracy number was corrected once after the benchmark itself was found to be flawed. |
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
