# Decisions

Why acri is small. Every capability that was proposed, considered, and kept or cut — with
the evidence that decided it.

This document exists because the easiest way for a small library to die is to accept every
good idea. Each row below is a good idea. Most are still cut.

**Status:** decided 2026-08-25. Anything here can be reopened with evidence — that is what
the `design:` issue template is for.

---

## The rule that decided most of these

Every major provider prices cached input at roughly a tenth of normal input, and the cache
is keyed on a **stable prompt prefix**.

That single fact kills any design that rewrites the prefix each turn:

| Design | Why it dies |
|--------|-------------|
| Swapping tool schemas every turn | New prefix every turn, cache never hits |
| Switching models mid-conversation | Cache is per-provider *and* per-model; switching starts from cold |
| Rewriting history to compact it | Mutates the prefix permanently |
| Mid-stream handoff through a summarizer | Mutates the prefix *and* paraphrases it |

So the governing rule is: **resolve once per task, freeze, append only.**

It also changes what acri is allowed to claim. When schemas are cached, they are cheap —
so "we save you tokens" is a weak claim. What caching does **not** fix is that the schemas
still occupy the context window, and the model still has to choose correctly among a large
toolset. Those are capacity and accuracy problems. **acri sells accuracy. Tokens are the
second number, never the headline.**

## The ledger

| # | Capability | Decision | Evidence |
|---|------------|----------|----------|
| 1 | Multi-LLM tier routing | **KEEP, small** | Route *before* generating, once per task. [Is Escalation Worth It?](https://arxiv.org/abs/2605.06350) finds a lightweight pre-generation router beats optimal cascade policies on 4 of 5 datasets. |
| 1b | Mid-stream interrupt + handoff | **CUT** | [Performance Drift from Model Switching](https://arxiv.org/abs/2603.03111) measures one clean handoff swinging Multi-IF strict success by double-digit points in both directions. Abort billing is undocumented at OpenAI and charged anyway elsewhere — the feature cannot be measured. |
| 2 | MCP compatibility | **KEEP — core** | MCP `tools/list` is the input format users already have. This is the reason acri can exist at all. |
| 2b | Tool-result cache with TTL | **CUT** | In an agent loop a cached `read_file(x)` served across your own `write_file(x)` returns pre-edit content. The agent then "fixes" a bug that no longer exists. |
| 3 | Inter-agent gRPC bus | **CUT** | Protobuf between two objects in one Python process is a function call with a codegen step. Serialization is a rounding error against a network call to a hosted model. |
| 4 | Per-agent budget caps / tool sandboxing | **CUT — idea is real** | Already shipped in-process: Pydantic-AI `UsageLimits`, Claude Agent SDK budget caps. Not acri's fight. |
| 5 | Kernel module / NPU / OS integration | **CUT** | Windows kernel drivers cannot be self-signed since Win10 1607; an EV certificate tied to a validated company is required, and post-CrowdStrike the platform direction is to move vendors *out* of the kernel. |
| 6 | Artifact / interactive HTML generator | **CUT** | A client rendering concern with no relationship to tool resolution. Structured output is already native on every provider. |
| 7 | Parallel agent orchestration | **CUT** | `asyncio.gather` is most of it, in the standard library. The rest is LangGraph's job, and it has a full-time team. |
| 8 | Semantic cache | **CUT permanently** | Not a performance feature with a quality knob — a correctness bug with a firing rate. "Is it safe to delete X" and "is it *unsafe* to delete X" sit within a hair of each other in embedding space. |
| 8b | Self-learning rules overriding the resolver | **CUT** | A rule layer with no exploration and no reward signal never re-tests itself, so it cannot be falsified. Failures arrive as "it got worse last week" and do not reproduce. A static, version-controlled overrides file does the useful part and stays debuggable. |
| 8c | Exact-match request cache | **KEEP, tiny** | Keyed on a hash of the full canonical request. Catches the real failure — identical calls repeated in a loop — without inventing similarity. |
| 9 | Parallel LLM + tool execution | **CUT** | Speculatively starting a tool before the model finished deciding to call it can fire a side effect that was never authorized. |
| 10 | Stable, future-proof API | **KEEP — as a constraint** | The way to keep an API stable is to keep it small. Stay `0.x` until exactly one thing is stable. Every capability added is a future breaking change. |
| 11 | Dispatch envelope from a fine-tuned classifier | **CUT the classifier** | Its fields already exist elsewhere: the target and confidence come from the retrieval score, and any context summary is written better by a model already in the loop. A classifier trained on a fixed label set also cannot name a tool registered after training. |
| 12 | A custom "ACRI Protocol" | **CUT** | A protocol with one implementation is a data structure. MCP earned the word because independent parties implement it. Revisit if a second implementation appears. |

**Kept:** MCP indexing, query-aware resolution, provider adapters, a small pre-generation
router, an exact-match cache. That is the library.

## Serialization: where TOON goes

[TOON](https://github.com/toon-format/toon) is real and well-built. It is also frequently
pointed at the wrong layer, including in an earlier draft of this project.

TOON's own README states that for deeply nested or non-uniform data, compact JSON often
wins outright. **JSON Schema tool definitions are exactly that shape** — nested and
non-uniform. Encoding schemas in TOON aims it at its documented worst case.

The headline comparison also needs care. TOON's advertised token reduction is measured
against pretty-printed JSON; against *compact* JSON — what every SDK actually sends — the
gap is far smaller (see their [benchmarks](https://github.com/toon-format/toon#benchmarks)).
Then note that schemas are cacheable, so a further reduction there is a fraction of an
already-discounted cost.

**Where TOON genuinely wins in acri:** tool *results*. Query rows, issue lists, time-series
— uniform tabular data, never cached, often very large. That is `press`, not `corpus`.

## Memory compression: where TurboQuant goes

[TurboQuant](https://research.google/blog/turboquant-redefining-ai-efficiency-with-extreme-compression/)
(Google Research, ICLR 2026) is a genuine advance in vector quantization, with two
applications: KV-cache compression and vector-index compression.

Neither reaches a client calling hosted APIs. **You cannot compress a provider's KV cache
— it runs on their servers.** And acri's own index is small enough at realistic tool counts
that compressing it saves an amount of memory no user will notice.

It becomes genuinely applicable the moment acri drives **local** models, where the KV cache
is ours. Since local models are also the users with no native tool search, that is a real
future path — on the roadmap, not in v0.1.

## The competitive clock

Two things are moving, and both argue for shipping something small quickly.

**MCP is pulling tool filtering server-side.** [SEP-1300 "Tool Filtering with Groups and
Tags"](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1300) closed as
completed on 2025-12-01. SEP-1821 (Dynamic Tool Discovery) and SEP-1881 (Scope-Filtered
Tool Discovery) also closed, and "Capability-Aware Tool Presentation" is open as of
2026-03-26.

Those are **static, server-declared** filters — groups, tags, scopes. acri does
**query-aware retrieval**: pick tools for *this* request, ranked against everything
registered right now. Different mechanism, and they compose. But the gap is narrowing.

**Someone has already tried this shape.** `openclaw-toolsearch` published to PyPI on
2026-03-07 as "Semantic Tool Discovery Middleware for MCP." Its dependencies — FastAPI,
uvicorn, SSE, JWT — make it a **server you run**, and it has not shipped a second release.
The problem is real enough that others reached for it; the form factor is still open.

**acri's daylight: an import, not a server.** No daemon, no port, no proxy, works offline.

## Roadmap

| Version | Scope |
|---------|-------|
| **v0.1** | `corpus` + `compass` + `port`. Index tools, resolve the right few, adapt to Gemini and OpenAI-compatible endpoints. Pure Python, no native dependencies. |
| **v0.2** | `ledger` + `assay`. Receipts, then benchmarks. Nothing is claimed before this ships. |
| **v0.3** | Pre-generation router (capability 1, the surviving half). Exact-match cache. |
| **later** | `press` with TOON for tabular tool results. Local-model support. TurboQuant only if local inference lands. |

## Dependencies we refuse

Named here so the refusal survives a future contributor's good intentions:

- **onnxruntime** — no musllinux wheels; Alpine users cannot install.
- **hnswlib** — source-only, needs a C++ toolchain on Windows, and buys nothing at
  realistic tool counts.
- **grpcio** — drags protobuf into every user's dependency resolution.
- **A bundled model file** — PyPI enforces a per-file size cap, serverless runtimes cap
  unpacked size, and air-gapped and corporate-proxy installs break in ways you cannot
  debug remotely.

If embeddings are wanted, the caller supplies the encoder. Anyone with hundreds of tools
already runs one.
