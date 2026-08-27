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

## Retrieval must never be the safety boundary

A tool described as "delete a table" and one described as "read from a table" both match the
query *"delete table users"* — on exact tokens **and** on meaning. No ranking function
separates them reliably, because they are genuinely similar. Better retrieval narrows that
gap; it never closes it.

So the boundary has to be somewhere else:

- **Retrieval decides what the model sees.** That is all it decides.
- **A destructive tool must be marked at registration** and require explicit confirmation
  before execution, no matter how confidently it was retrieved or how sure the model sounds.
- A ranking score is **never** an authorization. Rank 1 at 0.99 confidence is still just a
  suggestion about relevance.

This is the same rule as [architecture.md §4.3](architecture.md) — `gate` may influence what
is offered, never veto what is chosen — pointed the other way. acri is allowed to be wrong
about relevance. It is not allowed to be the only thing standing between a query and
`DROP TABLE`.

## Ranking: lexical first, dense second, fusion only with a receipt

Pure dense retrieval fails in two documented ways: semantically opposite queries collide
when they share vocabulary (*"delete table users"* / *"select from table users"*), and rare
exact tokens get smeared away (`v2`, `ec2` in `get_ec2_instances_v2`).

Both of those failures are arguments for the **lexical** half, which is why BM25 is the
default and ships with zero dependencies. Embeddings address a different failure — pure
synonym gaps where no token overlaps at all (*"check forecast"* → `get_weather`).

Sequencing, each stage earning its dependency:

| Stage | What | Gate to adopt |
|-------|------|---------------|
| 1 | BM25 alone | Ships in v0.1. No dependencies. |
| 2 | Optional caller-supplied encoder, fused with BM25 | Only if `assay` shows fusion beats lexical alone on a real MCP catalog |
| 3 | Hierarchical / tree routing | Not planned. Flat search degrades gracefully — a bad match still leaves the right tool at rank 4. Tree routing fails hard: route into the wrong branch and the right tool is unreachable at any k. Revisit only at catalog sizes where flat search measurably breaks. |

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
| **v1.0** | `daemon` — a long-lived process holding a warm index, exposing the same resolution over a local endpoint. See the rule below. |
| **v1.1** | `sandbox` — execute untrusted MCP servers inside a container with CPU, memory, and network limits, by **calling** the host container engine, never reimplementing one. |

### The two runtime modes, and the rule that keeps them honest

acri is meant to have exactly two modes:

| Mode | How it's used | Status |
|------|---------------|--------|
| **In-process library** | `import acri` — no process, no port, no daemon | **The product.** Ships first. |
| **Daemon** | `acri up` — long-lived service, warm index, local endpoint | Real, planned, **v1.0** |

**The rule: the daemon is a thin wrapper over the library, never a superset.** `acri up` must
call the same `resolve()` that `import acri` calls. The moment the daemon gains a capability
the library does not have, the library becomes the degraded option and the project has
quietly become a service.

That rule exists for a specific reason. The one comparable project that shipped this shape —
`openclaw-toolsearch`, PyPI 2026-03-07 — shipped it **as a server first** (FastAPI, uvicorn,
SSE, JWT) and has not published a second release. Requiring users to run a service before
they can try a tool resolver is the failure mode, not the feature. The whole competitive
position is *an import, not a service*; building the service first spends exactly that.

So the daemon is built **after** the library has users who want it, not before.

### On sandboxing MCP tools

Legitimate, and worth doing eventually — with two clarifications:

- **MCP already separates processes.** An MCP server is a subprocess or a remote HTTP
  endpoint, not code running inside your interpreter. The genuine gap acri would close is
  *resource and network limits* on stdio servers, not process separation.
- **Call the container engine; never write one.** Isolation comes from the host kernel's
  namespaces and cgroups, reached through the already-privileged container daemon. Writing
  that layer is writing `runc`.

### Two corrections to the proposed module layout

Recorded so they do not get re-litigated:

- **`compass` does not do tree routing.** See the ranking table above — flat search degrades
  gracefully, tree routing fails hard. Not planned.
- **`compass` does not do TOON encoding.** TOON goes to `press`, on tool *results*. Schemas
  stay compact JSON, for the reason in the serialization section below.

## Resolution does not understand the query — and must not

`compass` performs no language understanding. BM25 scores query terms against tool names and
descriptions, weighting terms that are rare across the corpus. It has no concept of what a
"pull request" *is*; it knows the token appears in few enough tool descriptions to
discriminate between them.

That is not a limitation to engineer away — it is the reason the design works at all.
Understanding costs a model call. The split:

| Stage | Job | Wrong in which direction |
|---|---|---|
| `compass` | **Recall.** Narrow N tools to k candidates. | May include irrelevant tools — the model discards them; the cost is tokens. |
| The model | **Precision.** Choose one, write its arguments. | Already its job today, unchanged. |

`compass` is allowed to be dumb because it is only allowed to be wrong in the cheap
direction. Missing the correct tool entirely is the expensive failure, which is why
`find_more_tools` is always present as an escape hatch (architecture §4.1).

**The metric that matters is recall@k, not resolver latency.** A resolver taking one
millisecond or ten is invisible against a network call — claiming otherwise is the same
Amdahl's-law error that cut the gRPC bus. A resolver with poor recall fails the agent
silently. `assay` measures recall first; latency is reported second and never headlined.

Hybrid ranking (lexical and dense scored in parallel, then rank-fused) is the eventual
shape, not a first step — see the ranking section above. v0.1 is BM25 alone.

## The privilege ladder — what "kernel level" can and cannot mean

Recorded because "register acri natively with the kernel" keeps returning, and the four
things it could mean have wildly different costs.

| Level | What it actually is | Gives you | Verdict |
|---|---|---|---|
| **1. Background service** | A `systemd` unit (Linux) or a Service Control Manager entry (Windows) | Starts at boot, survives logout, holds a warm index | **Yes — this is `daemon`, v1.0** |
| **2. Process isolation** | A subprocess holding no credentials, whose only channel is a pipe to the parent | Real enforcement: the child *cannot* reach the network itself | **Yes — this is `sandbox`, v1.1** |
| **3. Namespaces + cgroups** | Host-kernel features you *call*, through the container engine | CPU, memory, and network limits on untrusted tools | Linux only, reached through the container engine, never reimplemented |
| **4. Kernel module / driver** | Code executing in ring 0 | Nothing this project needs | **Never** |

Three things about that table matter more than the table.

**A systemd unit is not privileged.** `systemd` is a launcher. A service registered with it
has exactly the permissions of the user it runs as — the same permissions it would have if
the command were typed into a terminal. "Registered with the operating system" and "running
in the kernel" are unrelated statements, and only the first one is being offered.

**Namespaces and cgroups are host-kernel features, not shipped code.** A container does not
contain a kernel; it borrows the host's. So "ship the Linux kernel inside the image so acri
gets kernel-level permission" resolves to one of two things: on Linux it is redundant, the
kernel is already there; on Windows or macOS it means shipping a Linux **virtual machine**,
which is what Docker Desktop does — a hypervisor dependency and hundreds of megabytes, to
host a function whose work is measured in milliseconds.

**Ring 0 would not make anything faster.** A syscall costs on the order of a hundred
nanoseconds; a provider API round trip costs on the order of hundreds of milliseconds. No
arrangement of kernel code meaningfully changes a number dominated by a datacenter round
trip. On Windows the door is also shut: kernel drivers cannot be self-signed (Windows 10
1607 onward), require an EV certificate bound to a validated company, and Microsoft has been
reducing third-party kernel presence since the July 2024 CrowdStrike outage.

**What gives an agent power over a machine is the permission set on its tools, not its
ring.** An agent permitted to call `shell.exec` as root already has more reach than a driver
would grant it. That is a policy problem, and policy is what levels 1–3 address.

## Mediation is not enforcement

"A child agent raises a request to the parent, the way a process raises a syscall" is the
right shape, with one correction that has to survive contact with future contributors.

A CPU mode bit works because the hardware traps a privileged instruction issued from ring 3.
The child *cannot* proceed. That trap is what makes a kernel a security boundary.

If the child agent is a Python function in the same interpreter, it can `import httpx` and
call the tool directly. Nothing traps. In-process capability brokering is therefore
**cooperative** — it works because the child asked, not because it had to.

Still worth building. Cooperative mediation gives one place for quotas, one audit log, and
one policy decision instead of N scattered ones. It is `malloc` over `sbrk`: a convention
that pays for itself. It is simply not a boundary, and a document that calls it one will be
discounted by every reader who knows the difference.

| To get | You need |
|---|---|
| Quotas, audit trail, a single policy point | The convention. In-process, small. |
| Actual enforcement | A process boundary: no credentials in the child, one pipe out. This is `sandbox`. |
| Resource limits on untrusted code | Namespaces and cgroups, through the container engine. Linux. |

Enforcement and `sandbox` are the same feature, not two.

## Parallel execution — what is free and what is not

Concurrency while tools run is real, and it is `asyncio`, not a thread pool. Tool calls are
I/O; threads would add GIL contention and locking around a shared corpus for no gain.

| Case | Verdict |
|---|---|
| The model emits several tool calls in one turn | `asyncio.gather`. One line. Real win. |
| Independent agents running concurrently | Same mechanism. Free. |
| Running a tool the model has not asked for yet | **No.** |

The last row needs stating. The opportunity for parallelism is bounded by what the model
emits — if it requests one tool, there is nothing to overlap, and the wait is on the model,
not the tool. Speculating past that means paying for calls that get discarded, and worse: a
speculatively executed `send_email` sends an email. Any future speculative execution
requires an explicit `read_only` annotation on the tool, defaulting to false.

## `studio` — the trace visualizer

Accepted, with a boundary. It is the first proposed addition that cannot make the core
wrong, because it only ever reads.

- `ledger` emits structured events — resolution start, per-candidate scores, tool start and
  finish, model call with token counts — as JSONL.
- `studio` is a **separate optional install** (`pip install pyacri[studio]` — PyPI's
  distribution name; `import acri` and the `acri` command are unaffected, see
  pyproject.toml) that consumes that stream. The core never imports it.
- Off by default. Live mode tails the ledger, or subscribes to a local socket the core
  publishes to **only when a subscriber exists**.
- Two views: the static mesh — every registered capability, model, and MCP server — and the
  live trace, showing one request moving through resolution, model, and tools.

Why it earns its place when so much else did not:

1. It is the product surface for `ledger`. Nobody adopts a JSONL file.
2. It is the demo. One recording of resolution happening live does more for adoption than
   another design document.
3. **It makes the claims falsifiable in public.** When `compass` picks a bad tool, the user
   watches it happen. For a project whose origin was a document full of invented benchmark
   numbers, an honesty device that runs by default in development is worth building.

Two corrections to the proposal:

- **Not "zero overhead."** Writing ledger events costs serialization and I/O even with nobody
  watching. Small, and off the hot path if buffered — but it is a number, and numbers in this
  repo come from `assay/` runs.
- **Emit OpenTelemetry spans, not a private format.** The trace shape is a solved standard.
  Spans mean Jaeger, Grafana Tempo, and Honeycomb work at no cost, and `studio` becomes one
  consumer among several rather than the only way to see anything.

**Built 2026-08-26.** `acri/studio.py` + `acri/studio_data.py` — see `architecture.md` §4.5
for exactly which parts of this proposal shipped as designed and which are honestly
thinner (the ledger schema below its full description here; the static mesh shows tools
*seen* in ledger history, not a live-queried catalog of everything a server declares).
The OpenTelemetry migration two paragraphs up is still not done.

The boundary to hold: **`studio` may only display what `ledger` would record anyway for
debugging.** When the visualizer wants a new field, the test is "would this belong in a bug
report?" If not, it is not emitted. Otherwise the observability layer starts dictating the
shape of the core, which is how observability layers metastasize.

## The daemon's HTTP surface

When `daemon` lands, its endpoint is **OpenAI-compatible** (`/v1/chat/completions`) — the
lazy choice with the largest payoff. The OpenAI SDK, LangChain, LlamaIndex, Cursor,
Continue, Open WebUI and plain `curl` already speak it. vLLM, Ollama, and LM Studio all made
the same call.

The streaming flow, written down because it is routinely misdescribed:

1. The request arrives. Resolution runs **before any token is generated** — it is not inside
   the token stream.
2. Tokens stream back over server-sent events.
3. The model emits a tool-call block and **stops generating.** The pause a user perceives
   here is the tool's own latency plus one additional provider round trip. It is not acri
   overhead, and acri cannot remove it.
4. The tool result is appended as a new message; generation resumes.

Two obligations that arrive with being in the request path, recorded now because they are
easy to forget later:

- **Bind to localhost by default.** A capability resolver holding provider credentials and
  listening on `0.0.0.0` is a credential proxy for the whole network.
- **Never log message bodies at the default level.** `ledger` records decisions, scores, and
  token counts. Conversation content is opt-in.

A library that fails to import fails loudly, at startup, on the developer's machine. A daemon
that goes down takes the application with it. That asymmetry is why the library ships first
and the daemon stays a thin wrapper over it.

## Agents are capability nodes, and this costs nothing

`corpus` indexes a name, a description, and a schema. It neither knows nor cares whether the
thing behind that name is a Python function, an MCP tool, an HTTP endpoint, or another agent.
So "connect an existing LangChain or AutoGen agent into the mesh" needs **no new machinery in
`compass`** — it is a `corpus` entry plus an invoke path in `port`.

That property is already true of the v0.1 design and belongs in the README, because it is the
cheapest large capability in the project.

What not to build: framework-specific adapters, preemptively. Each is a dependency on
somebody else's fast-moving API. acri accepts **any callable** and **any HTTP endpoint**; a
user with a LangChain agent wraps it in a function in three lines. Ship an adapter when an
issue asks for one, named after the framework that asked.

Dispatch is a function call or an HTTP request. Not gRPC — see the refusals below.

## `acri.yaml` — declarative configuration

Accepted, and possibly the most important adoption decision in the project. People learn
Docker by learning `docker-compose.yml`. The file *is* the mental model; the API is an
implementation detail. If acri is meant to be learned the way Spring Boot and AWS are
learned, the thing being learned is a file format.

It declares what exists:

```yaml
version: 1
models:
  default: gemini-2.5-flash
  cheap:   gemini-2.5-flash-lite    # stateless calls only — architecture §4.4
mcp:
  - name: github
    command: ["npx", "-y", "@modelcontextprotocol/server-github"]
  - name: postgres
    url: http://localhost:3001
resolve:
  k: 5
limits:
  timeout_ms: 5000
  max_cost_per_task_usd: 0.05
```

Two boundaries:

**It declares capabilities and limits. Never control flow.** The moment the file grows
`steps:`, `on_error:`, or conditionals, it is a programming language expressed in YAML, and
every tool that took that road regrets it. `docker-compose.yml` has aged well precisely
because it only ever declared services.

**`max_cost_per_task_usd` is a budget check, not a cgroup.** It is a running token count and
a refusal to make the next call — cooperative, bypassable, and genuinely useful. Naming it
after a kernel primitive invites the reader to expect enforcement that is not there.

The setup experience is `acri init`, which writes a commented template, and `acri check`,
which validates it and names the credentials that are missing. That is most of the value of
an interactive wizard for a fraction of the code. A full terminal wizard can follow if anyone
asks for one.

### The builtin tool pack — opt-in, not on by default

`tools: builtin: [press.digest]` loads acri's own tools (`acri/builtin.py`) into the same
corpus as `mcp:` entries. Silence means none load, same posture as `mcp:` itself. Only
`press.digest` ships — `sandbox.run` was considered and rejected because sandbox config
isn't a tool in the MCP sense (see `docs/research/future-work-tool-pack.md` for the
reasoning that shaped this before it was built). Kept out of the paper's evaluation corpus
deliberately: the accuracy numbers there measure resolving a caller's *own* tools, and a
first-party pack is a separate surface with its own versioning obligations.

## Languages

One, for now: **Python.**

Every additional language is a second build matrix, a second test suite, a second release
process, and a permanent risk of the two implementations drifting apart — carried by a
project with no users yet.

| Language | When |
|---|---|
| **Python** | Now. |
| **TypeScript** | A real gap, and the JavaScript agent ecosystem is large. Port after the Python package has users, never in parallel with it. |
| **Rust / C++** | Only if `assay` shows Python ranking is a measurable share of a turn. Against a network call that dominates it, that is close to arithmetically impossible. |

The sandbox does not change this. Namespaces and cgroups are reached by calling the container
engine, which is a subprocess call — available from Python without a compiler.

## The claim, in one sentence

Draft summaries have accumulated several claims at once: lower cost, faster execution, better
memory, higher accuracy, no hallucination. Sorted by whether they can be defended:

| Claim | Status |
|---|---|
| Improves tool-selection accuracy on large toolsets | **Measured — see README.md.** `assay/accuracy.py`, gemini-2.5-flash: naive 84%, acri 92%, a single run, after three corrected rounds (run history below). Not three-arm — "cache-enabled" was cut; caching changes cost, not which tools the model sees. |
| Frees context-window capacity | **Earnable.** Schemas occupy the window regardless of what they cost. |
| Works where the provider ships no native tool search | **A fact**, not a claim. Free to state. |
| Lowers cost | **Only against a named baseline.** Against a cache-enabled baseline it is false below roughly a tenfold reduction — see the rule at the top of this file. |
| Faster execution | **Not directly.** A resolver runs against a network call that dominates it. The defensible version is *fewer turns*: a model that picks correctly the first time does not spend a turn recovering. Second-order, and a better story. |
| Runs 24/7 cheaply | **A daemon property**, not a resolver property — no polling, no model held warm. |
| Better intelligence, no hallucination | **Not claimable.** A smaller choice set makes wrong choices rarer, not impossible. One counterexample destroys an absolute claim. |

**Accuracy run history**, kept in full because the corrections are part of the evidence:

| Run | naive | acri | What changed to get here |
|---|---|---|---|
| 1 (retracted) | ~24% | ~53% | Broken, see `assay/accuracy.py` commit history: all 100 tool schemas had empty `properties`; the model was correctly declining to fabricate arguments it was never given, scored as a miss. |
| 2 | 72% | 74% | Fixed: real JSON Schema on all 100 tools, every gold query supplies a value for each *declared* `required` field. Still left a gap `assay/diagnose.py` hadn't been run against yet. |
| 3 (current) | 84% | 92% | A `compass.py` synonym layer took recall@5 to 100% (`assay/recall.py`), then a diagnostic pass (`assay/diagnose.py`) on the resulting model misses found 9 more queries that satisfied their tool's `required` list on paper but still withheld a value the action needed in practice. Fixed per-case: |

The 9, each a real gap between "technically required" and "actually needed":

| Query (before) | Tool | What was missing |
|---|---|---|
| "is PR 42 merged into main yet" | `github_get_pull_request` | no repo — added `on the acme/webapp repo` |
| "email the invoice PDF to billing@acme.com..." | `email_send_email` | tool has no attachment field at all — reworded to a request the tool can actually do |
| "schedule a meeting with the design team tomorrow" | `calendar_create_event` | `start_time` not concrete — added `at 2pm` |
| "instance i-0abc123 is too small, bump it up a size" | `aws_ec2_resize_instance` | no target type — added `to t3.large`; `new_type` also marked `required` |
| "we need more replicas of the checkout-service deployment" | `kubernetes_scale_deployment` | no count — added `to 6 replicas`; `replicas` also marked `required` |
| "point api.example.com at the new server" | `dns_create_record` | no address — added `, 203.0.113.42`; `value` also marked `required` |
| "text +14155550101 their order confirmation" | `twilio_send_sms` | no message body — added `saying their order has shipped and will arrive Friday` |
| "this photo is low-res, can we sharpen it up" | `image_gen_upscale_image` | no file at all — became `sunset.jpg is low-res...` |
| "move the Acme Corp deal to the next sales stage" | `salesforce_update_opportunity` | no opportunity ID, no target stage — became `move opportunity opp_4471 (Acme Corp) to the Negotiation stage` |

**What was deliberately left alone**, because the gold tool's `required` fields were already
fully present and the model still declined — that's not a fixture bug, it's the model being
cautious about a consequential action:

- `"give customer cus_18x their money back"` → `stripe_refund_charge` (`customer_id` given)
- `"spin up a new EC2 box for staging"` → `aws_ec2_launch_instance` (nothing is `required`)

Both still miss in run 3. Patching them further — inventing a specific refund amount or
instance size the query never implied — would stop being a benchmark fix and start being
tuning toward a number. Held the line there on purpose, same as the two BM25 recall misses
this project has never chased. If this shape (declines a write action with everything it was
given) shows up again elsewhere, it's a finding about the model, not this fixture set.

The defensible sentence:

> acri is a client-side capability resolver. Given a query and hundreds of registered tools,
> it selects the few that matter before the request is sent — improving tool-selection
> accuracy for providers that ship no native tool search, without invalidating the provider's
> prompt cache.

**The strongest contribution is the constraint, not the resolver.** Retrieval over tool
schemas is published work (see architecture §6). What is not published is the consequence of
prompt caching: per-turn tool retrieval *increases* cost, and the break-even is a reduction
factor on the order of the cache discount. That finding reframes a whole category of "context
optimization" work, and it is the part of this project nobody else has said.

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
