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
├── router    the tier picker — cheap/strong model, chosen once, before generating
├── port      provider adapters — gemini · openai-compatible (OpenAI, vLLM, Ollama, ...)
├── config    acri.yaml — declares capabilities and limits, never control flow
├── daemon    the OpenAI-shaped request handler — acri.run(), nothing more
├── server    `acri up` — binds it: stdlib http.server, SSE, localhost by default
├── gate      the necessity check — does this turn need a tool at all?  (advisory)
├── press     the compactor — big payloads to short digests + a handle
├── ledger    the decision trace — what was chosen, skipped, and what it cost
└── assay     the proving ground — the only place a benchmark number may come from
```

## Status

**Pre-alpha — API not yet stable (v0.x, see `docs/decisions.md`). `corpus` + `compass` +
`port` + `ledger` + `assay` + an exact-match cache + a pre-generation router all exist,
are tested, and back every claim below with a script or a test file. `daemon` (`acri up`)
exists too, ahead of its own gate — see the v1.0 roadmap row for what that means.**

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
| 1 | 74% — [`assay/recall.py`](assay/recall.py) | 1 |
| 3 | 90% — [`assay/recall.py`](assay/recall.py) | 3 |
| 5 | 100% — [`assay/recall.py`](assay/recall.py) | 5 |
| 10 | 100% — [`assay/recall.py`](assay/recall.py) | 10 |

Both adversarial queries (no correct tool exists in the corpus) correctly resolve to
nothing, at every k. The k=5 row moved from 86% to 100% ([`assay/recall.py`](assay/recall.py))
after a small query-side synonym table was added to `compass.py` —
[`_ALIASES`](acri/compass.py), 10 entries, each traced to
a real miss, not guessed (`pr` → `pull`, `request`; `rain` → `weather`; `text` → `sms`,
`message`; and so on). It expands the query only, never the indexed tool text, so a tool's
own description can't start quietly matching a synonym it never claimed.

Recall says the right tool is *available* to the model in a much smaller set — not that
the model picks it. That's a separate, live-model question:
[`assay/accuracy.py`](assay/accuracy.py), naive (all 100 tools) vs. acri (top 5), same 50
queries, real `gemini-2.5-flash` calls, no mocking.

**Corrected twice, both times in public.** The first published number here claimed acri roughly doubles accuracy: naive ~24%, acri ~53% (commit history on [`assay/accuracy.py`](assay/accuracy.py)). That was a broken benchmark: every one
of the 100 fixture tools had an *empty* parameter schema, so a well-behaved model correctly
declined to fabricate a ticket ID or a SQL string it was never given, and that correct
caution was scored as a tool-selection failure. Fixing the schemas and the obviously
under-specified queries produced a second number: naive 72%, acri 74% ([`assay/accuracy.py`](assay/accuracy.py)), that this README called modest and honest. It
was honest, but still not fully clean: a live diagnostic pass
(`assay/diagnose.py`) surfaced 9 more queries that satisfied their tool's *declared*
`required` fields but still left a genuinely necessary value unstated — "bump it up a size"
with no target size, "point \[domain\] at the new server" with no address, an opportunity
referenced by company name instead of ID. Full list and reasoning:
[`docs/decisions.md`](docs/decisions.md). Fixed the same way as the first round — supply the
missing value, or mark the field `required` if the action is meaningless without it — never
by rewording toward the answer. Third run, current:

| Arm | accuracy | median latency |
|---|---|---|
| naive (100 tools) | 84% — [`assay/accuracy.py`](assay/accuracy.py) | 1792 ms |
| acri (top 5) | 92% — [`assay/accuracy.py`](assay/accuracy.py) | 1596 ms |

**An 8-point gap this time, not noise** — for scale, naive's own score moved 2 points
between the previous two runs with zero code changes on its side, so 2 points is this
benchmark's rough noise floor at n=50; 8 is well outside it. `assay/diagnose.py` confirms
`resolver_miss=0` — every remaining acri miss is the model's, not compass's — and all four
share one shape: the model declines to act (`picked: None`, not a wrong tool) on a
write/mutating request — refund a charge, launch a server, send an email, book a meeting —
even once every *required* field is present. That reads as the model being conservative
about consequential actions specifically, not a resolver or benchmark defect, and it is left
unpatched on purpose: supplying more certainty than a real caller would have crosses from
fixing the benchmark into fixing the test until it passes. This is still a single run at each
stage; repeat runs would firm up the interval and are a natural next step, not yet taken.
Reproduce: `GEMINI_API_KEY=... python -m assay.accuracy --provider gemini`, or via
[Vertex AI / ADC](assay/clients.py):
`GOOGLE_APPLICATION_CREDENTIALS=... GOOGLE_CLOUD_PROJECT=... python -m assay.accuracy --provider vertex`.

What this means for the project's claims: **recall — the context-window reduction — remains
the number that survived every round unaffected** (BM25 never reads a tool's parameters, so
none of the query-completeness fixes could have moved it; only the synonym layer did, on
purpose). The accuracy claim is now both real and no longer small, but it took three
corrected rounds to get a benchmark that measures tool selection instead of measuring
whether the fixtures gave the model enough to work with — a fact worth remembering before
trusting the next number this project publishes, including from this project's own authors.

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

### Diagrams

![acri resolution flow: corpus.index once, compass.resolve per query, top 5 of 100 tools sent to port](https://raw.githubusercontent.com/INERATE/acri/main/docs/assets/resolution-flow.svg)

![acri benchmark results: recall@k and naive vs acri tool-selection accuracy, both linked to their assay scripts](https://raw.githubusercontent.com/INERATE/acri/main/docs/assets/benchmark-results.svg)

Both are static SVGs generated from the numbers above, nothing more — no simulator, no live
trace, no feature these diagrams show that isn't already shipped and linked to the script
that measured it. If a future version adds `studio` (the real trace visualizer — see
[`docs/decisions.md`](docs/decisions.md)), it replaces these; until then, these are it.

### Roadmap

| Version | Scope | Gate to ship |
|---------|-------|--------------|
| **v0.1** | `corpus` + `compass` + `port` + minimal `ledger` | **Shipped.** `pytest` green, no native deps. |
| **v0.2** | `assay` | **Shipped.** Recall, latency, and a live accuracy result, all above — the accuracy number was corrected twice after the benchmark itself was found to be flawed, both times in public. |
| **v0.3** | Pre-generation router, exact-match cache | **Shipped.** Cache: `acri.run(..., cache={})` skips a repeated (provider, model, query, offered tools) call — [`acri/port.py`](acri/port.py)'s `cached_call`. Router: `acri.run(..., cheap_model=...)` routes one call to a cheaper tier, once, before generating — [`acri/router.py`](acri/router.py). Eligibility (is this call stateless and prefix-free?) is the caller's judgment, not acri's — see `docs/architecture.md` §4.4. Tests: [`tests/test_ports.py`](tests/test_ports.py), [`tests/test_router.py`](tests/test_router.py), [`tests/test_integration.py`](tests/test_integration.py). |
| **later** | `gate`, `press`, `studio` | Only if `ledger` data proves they are needed |
| **v1.0** | `daemon` — long-lived process, OpenAI-compatible HTTP endpoint | **Shipped, ahead of its own gate.** `docs/decisions.md`: "the daemon is built after the library has users who want it, not before" — not met (no PyPI release yet), and built anyway at the maintainer's explicit request; that override is deliberate, not an oversight. `acri up` ([`acri/server.py`](acri/server.py), stdlib `http.server` only) connects to `acri.yaml`'s `mcp:` entries once at startup ([`acri/mcp_connect.py`](acri/mcp_connect.py)), then serves `/v1/chat/completions` over SSE via [`acri/daemon.py`](acri/daemon.py)'s handler — the same `acri.run()` the library calls, not a reimplementation. Binds `127.0.0.1` by default; conversation content is opt-in (`--log-conversations`), off by default via `RedactingLedger`. Verified against a real MCP server and a real Gemini call, not just fakes — which surfaced and fixed a real bug: Gemini's function-calling schema rejects the `$schema` key real MCP servers commonly add, invisible to every synthetic fixture in this repo (`acri/schemas.py`). Tests: [`tests/test_config.py`](tests/test_config.py), [`tests/test_cli.py`](tests/test_cli.py), [`tests/test_daemon.py`](tests/test_daemon.py), [`tests/test_server.py`](tests/test_server.py), [`tests/test_schemas.py`](tests/test_schemas.py). Wire-level SSE only — one blocking `acri.run()` call chunked out, not a true streaming upstream call. |

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
