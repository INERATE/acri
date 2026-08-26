# acri architecture

**Status:** design. No code yet. This document is an argument, and it is meant to be
argued with — see the `design:` issue template.

---

## 1. The problem, stated precisely

An agent with many tools has to get every tool schema into the model somehow. The default
answer is: put all of them in every request. That answer breaks in three ways.

**It breaks selection accuracy.** Anthropic's documentation states plainly that a model's
ability to pick the right tool degrades once the toolset exceeds roughly 30–50 tools. This
is the failure that matters most, because it is silent — the model picks a plausible wrong
tool and proceeds confidently.

**It wastes the context window.** Schemas the model will never use this turn still occupy
budget and still compete for attention.

**It is already solved, but not for everyone.** Anthropic ships
[tool search](https://docs.claude.com/en/docs/agents-and-tools/tool-use/tool-search-tool);
OpenAI ships an equivalent. Gemini does not. Ollama, vLLM, llama.cpp and every local model
do not. A developer on Gemini or an 8B local model has no answer at all.

**acri exists for that gap.** Same capability, client-side, provider-agnostic.

## 2. What acri does

```
your app  ──►  acri  ──►  provider API
                 │
                 └─ decides which tools this request carries
```

One function call. No process to run, no port to open, no network hop, no framework to
adopt. On Anthropic, `port` passes through to the native feature instead of duplicating
it — shipping that pass-through is how we prove our semantics match a real implementation.

## 3. The components

| Component | Responsibility |
|-----------|----------------|
| **`corpus`** | The capability index. Ingests MCP servers, OpenAPI specs, and plain functions into one searchable body. Built once, reused across turns. |
| **`compass`** | The resolver. Given the query and the session state, returns the k tools that matter. **This is the product.** |
| **`port`** | Provider adapters. Gemini, OpenAI-compatible (vLLM, Ollama, together), Anthropic pass-through, local. ~50 lines each. |
| **`gate`** | The necessity check — does this turn need a tool at all? Advisory only. |
| **`press`** | The compactor. Large tool payloads become a short digest plus a handle to the full result. |
| **`ledger`** | The decision trace. What was chosen, what was skipped, what it cost. The receipts. |
| **`assay`** | The proving ground. The only place in this project a benchmark number may originate. |

`corpus` + `compass` + `port` is v0.1 and is a complete product on its own. The rest are
built only if `ledger` data shows they are needed.

## 4. Three design decisions, and why

### 4.1 Resolve once per task, not once per turn

The obvious design re-runs retrieval every turn and swaps the tool block each time. **That
design costs more than doing nothing**, and this is the single most important correction in
this document.

Every major provider prices cached input tokens at roughly a tenth of normal input tokens,
and the cache is keyed on a stable prefix. The tool block sits at the front of the request.
Rewriting it every turn invalidates the cache on every turn, so a "smaller" prompt gets
billed at full rate while a larger unchanged prompt gets billed at the cached rate.

Reducing the prompt to a fraction `r` of its size, at full price, beats a fully-cached
baseline only when `r` is below the cache discount — roughly a **tenfold** reduction. Below
that threshold, sending everything and letting the cache work is cheaper.

So: **resolve at task start, write the tool block once, append after that.** Never rewrite
a prefix that has already been sent.

There is an escape hatch. `compass` always includes a `find_more_tools` capability, so a
bad initial resolution is recoverable by the model mid-task rather than trapping it.

### 4.2 The gate goes *after* retrieval, never before

Whether a turn needs a tool is a function of three things: the query, the session state,
and **which tools are actually registered.** "What's the weather in Tokyo?" needs a tool if
a weather tool exists and does not if none does — same input, opposite correct answer.

A classifier that sees only the query cannot condition on the registered toolset. No amount
of training data fixes that; the information is not in its input. It also goes stale the
moment a developer registers a tool it was never trained on, and can only be repaired by
retraining and reshipping.

Retrieval already computes the signal we need: the top similarity score against the tools
that are *actually registered right now*. A new tool works the instant it is indexed.

So the pipeline is **retrieve → score → gate**, and `gate` is a threshold on a number the
system already has, not a separate model with its own opinion.

### 4.3 `gate` is advisory and can never suppress a call

The two failure directions are not symmetric.

A false *"a tool is needed"* costs a few tokens and appears in the trace. A false *"no tool
needed"* makes the model answer "what is my account balance?" from parametric memory:
fluent, confident, wrong, with **no exception, no retry, and nothing in the logs**.

Therefore nothing in acri may block a tool call the model wanted to make. `gate` may
influence what is offered; it may never veto what is chosen.

### 4.4 Route before generating, never mid-stream

acri picks a model the same way it picks tools: **once, before work starts.**

Routing cheap turns to a cheap model is a real technique.
[Is Escalation Worth It?](https://arxiv.org/abs/2605.06350) finds that a lightweight
*pre-generation* router beats optimal cascade policies on 4 of 5 datasets — because a
cascade has already paid the cheap model before it decides to escalate.

What acri will not do is interrupt a model mid-answer and hand the partial response to a
stronger one. Three things break it:

- **You cannot measure it.** Billing on stream abort is undocumented at one major provider
  and charged regardless at the others, and usage totals arrive only in the final chunk.
- **It is not portable.** "Continue from this partial response" changed shape between two
  adjacent model versions *within a single vendor*, and has no equivalent elsewhere.
- **It costs quality.** [Performance Drift from Model Switching](https://arxiv.org/abs/2603.03111)
  measures a single clean handoff moving multi-turn instruction-following by double digits
  in *both* directions. Mid-sentence, through a paraphrase, is strictly worse.

And it violates §4.1: caches are keyed per provider *and* per model, so any switch starts
from a cold prefix.

The surviving rule:

- Route **once per task**, before generation.
- Route only **stateless, prefix-free** calls to the cheap tier — classification,
  extraction, summarizing a tool result. There the cheap model competes honestly.
- On failure, **re-run the original unmodified prompt** on the strong model so its cache
  still hits. Never continue from the failed attempt.

## 5. What this design is not

- **Not a microkernel, kernel, runtime, or OS.** Those words denote privilege boundaries,
  address spaces, and scheduling. acri has none of them. It is a library that decides the
  contents of a request. An earlier draft of this design used that vocabulary; it was
  marketing, and it is gone.
- **Not a gRPC bus.** Protobuf saves microseconds per hop against an API call measured in
  hundreds of milliseconds. It would add a build toolchain, a port, and an interop story
  for a rounding error. Cut.
- **Not a native C++/Rust core.** The candidate hot-path libraries are already native with
  maintained bindings. Writing native code to call native code, to save a fraction of a
  percent of a turn dominated by network latency, buys nothing and costs a per-platform
  build matrix forever. Cut.
- **Not a bundled model.** Shipping a large ONNX file inside a package breaks size limits,
  air-gapped installs, and per-platform wheels. If embeddings are wanted, the user supplies
  the encoder — anyone with hundreds of tools already runs one.
- **Not an agent orchestrator.** No graph, no agent loop, no parallel task planner. That is
  LangGraph's job and it has a full-time team. acri is called *by* an orchestrator.
- **Not a protocol.** A wire format with exactly one implementation is a data structure.
  MCP earned the word because independent parties implement it. Revisit if a second
  implementation of acri's semantics ever appears.
- **Not a semantic cache.** Serving a stored answer for a *similar* question is not a
  performance feature with a quality knob; it is a correctness bug with a firing rate. A
  question and its negation sit close together in embedding space. Exact-match on a hash of
  the full canonical request is the only caching acri will do.

The full list of what was proposed and cut, with the evidence for each, is in
[decisions.md](decisions.md).

## 6. Prior art

acri is a placement argument, not a novelty claim. The technique is published.

- **[RAG-MCP](https://arxiv.org/abs/2505.03275)** (2025) — retrieval over tool schemas to
  mitigate prompt bloat. This is `corpus` + `compass`.
- **[When2Call](https://arxiv.org/abs/2504.18851)** (NAACL 2025) — when (not) to call
  tools. This is `gate`, and it is where the taxonomy comes from.
- **[Anthropic tool search](https://docs.claude.com/en/docs/agents-and-tools/tool-use/tool-search-tool)**
  and **[context editing](https://docs.claude.com/en/docs/build-with-claude/context-editing)** —
  the same ideas, shipped provider-side.
- **[Agentic Routing](https://arxiv.org/abs/2607.11399)** (2026) — routing conditioned on
  full execution state rather than the query alone. Independent support for §4.2.

What acri contributes is the **form factor**: in-process, zero-daemon, framework-agnostic,
and available on providers that ship nothing equivalent.

## 6.5 Where the niche stands

Two forces are closing on this space, and both argue for shipping something small soon.

**MCP is moving tool filtering server-side.**
[SEP-1300, "Tool Filtering with Groups and Tags"](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1300),
closed as completed on 2025-12-01; SEP-1821 (Dynamic Tool Discovery) and SEP-1881
(Scope-Filtered Tool Discovery) followed. Those are **static, server-declared** filters —
groups, tags, scopes, fixed before the query exists. acri does **query-aware retrieval**:
rank everything registered against *this* request. The two compose rather than compete,
but the gap is narrowing.

**Others have reached for this shape.** `openclaw-toolsearch` published to PyPI on
2026-03-07 as semantic tool-discovery middleware for MCP. Its dependency list — a web
framework, an ASGI server, SSE, JWT — makes it **a server you run and operate**, and it has
not shipped a second release.

acri's daylight is the form factor: **an import, not a service.** No daemon, no port, no
proxy, works offline, and it never becomes another thing to deploy.

## 6.6 Serialization

Tool schemas stay as compact JSON. [TOON](https://github.com/toon-format/toon) is a strong
format, but its own documentation says compact JSON often wins outright for deeply nested,
non-uniform data — which is exactly the shape of a JSON Schema tool definition. Its
advertised savings are also measured against pretty-printed JSON rather than the compact
JSON every SDK actually sends.

Where TOON earns its place is **tool results**: uniform tabular data such as query rows or
issue lists, which are never cached and are frequently the largest thing in the context.
That belongs to `press`, and lands with `press`. See [decisions.md](decisions.md).

## 7. Claims this project does not make

Recorded here so nobody has to relitigate them later:

- No latency multiple. A resolver runs against a network call that dominates it. Any
  end-to-end speedup claim would be an Amdahl's-law error.
- No blanket cost reduction. Against a cache-enabled baseline, token reduction below
  roughly tenfold is a **regression**, not a saving. See §4.1.
- No "O(1) context growth". Per-request context can be bounded to a constant; total tokens
  processed across a conversation remain linear in turns. Attention cost within a request
  is quadratic in its length. These are three different statements and conflating them is
  an error.
- No claim to enable tool use in models that lack it. Constrained decoding and structured
  outputs solved that years ago.

The one claim acri intends to earn is **tool-selection accuracy on large toolsets for
providers without native tool search**, measured against a two-arm baseline: naive
(every tool shown) and acri (only the resolved k shown). An earlier draft of this
document specified a third "cache-enabled" arm; that was wrong and has been removed —
prompt caching changes what a call costs, not which tools the model sees, so it cannot
change which tool gets picked. It was a cost question wearing an accuracy question's
clothes. See [`assay/accuracy.py`](../assay/accuracy.py).

## 8. Open questions

1. **Ranking method.** Lexical (BM25) is zero-dependency and surprisingly strong on tool
   descriptions. Embeddings need a user-supplied encoder. Default should be decided by an
   `assay` run, not by taste.
2. **What `compass` sees.** Query alone, or query plus recent turns? §4.2 argues state
   matters; the cost of including it is unmeasured.
3. **Choosing k.** Fixed, or adaptive on the score distribution?
4. **Re-resolution triggers.** §4.1 forbids per-turn re-resolution. Some trigger must exist
   for genuine task shifts. What is it, and can it be detected without a model call?
5. **`press` fidelity.** Any digest can drop the one identifier a later turn needed. That
   failure is intermittent, which makes it the hardest kind to catch.
