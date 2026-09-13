# ACRI product plan and continuation log

Updated: 2026-09-13. Owner: Piyush Sharma. Working tree: `E:/Framework/acri`.

## Objective and rules

Make ACRI a lightweight, reliable capability layer that developers can integrate
into real agents. Product correctness comes first; research measures the product.
The owner explicitly authorized careful implementation and registry updates.
Ponytail full and Atelier review/clean-code guidance apply. Work inline; do not
delegate without authorization. Keep the dependency-free resolver and public APIs.
Do not promise novelty, zero hallucinations, journal acceptance, funding or stars.
Do not add orchestration or caching merely to enlarge the feature list.

## Resume here

- Base commit inspected: `f708f6e`, branch `main`; initially clean working tree.
- Read `git status --short` and this file before resuming. Preserve existing edits.
- Release candidate: Python `0.7.1`, TypeScript `0.1.1`, Rust `0.1.1`.
- Fixed and reproduced before editing: redacted logging rejected `corpus_size`;
  schema changes reused stale response-cache entries; server ignored configured
  default model; Python/TypeScript accepted invalid retrieval limits.
- Latest local checks: 139 Python tests, 6 TypeScript tests, 9 Rust tests pass.
  npm pack and Cargo publish dry-runs pass. Python wheel/sdist build and twine checks pass.
- CI now runs all three language suites; registry publishing depends on this CI.
- No versions published yet in this session. Previously live: Python `0.7.0`,
  TypeScript and Rust `0.1.0`. Verify workflows and registries before updating this line.
- PDF and Crawl4AI evidence are outside the package at `E:/Framework/acri-audit`:
  `paper.pdf`, `paper.txt`, `site.html`, `acri-crawl.md`, `toolret-crawl.md`.
  Crawl4AI ran successfully in an isolated uv environment; no dependency added here.

## Ordered work

### 1. Correctness patch and honest documentation

- [x] Inspect resolver, corpus, provider dispatch, cache, daemon, escape hatch,
  ledger, evaluation runner, manifests and publishing workflow.
- [x] Reproduce and fix default redacted logging failure with an end-to-end test.
- [x] Fix schema-sensitive response cache identity in `acri/__init__.py`, reusing
  schema serialization. Do not serialize when cache is disabled. Document that
  caller-owned caches must be isolated by client, tenant and task; clear on changes.
- [ ] Review cache client isolation and mutable response reuse before treating the
  response cache as enterprise-safe. Keep caching opt-in, with explicit limitations.
- [x] Remove README guarantees about hallucination prevention, destructive access,
  automatic task freezing and guaranteed provider cache discounts.
- [x] Save paper/code discrepancy review with primary-source links.
- [ ] Run Python suite, TypeScript tests, Rust tests, packaging and existing CI checks.
- [ ] Patch-version only affected packages; publish through existing GitHub workflow
  after checks pass; verify registry artifact versions and installability afterward.

### 2. Complete code audit

- [ ] Read remaining source and tests, recording each inspected module. Trace all
  callers before changing a shared function; add a failing regression for real bugs.
- [ ] Inspect ingestion: duplicate names, invalid schemas, empty text, MCP naming,
  OpenAPI claims, corpus mutation and cross-language behavior.
- [ ] Inspect retrieval: invalid k, tie stability, synonym evaluation leakage,
  memory/latency at large catalogs and TypeScript argument-spread limits.
- [ ] Inspect providers/server: conversation loss, error translation, credentials,
  request limits, timeouts, transport/stream semantics and truthful supported scope.
- [ ] Inspect builtin tools, sandbox, press/recover, config and CLI for filesystem
  escape, unsafe execution, payload loss, resource ceilings and secrets in logs.
- [ ] Inspect release workflow: all-language tests, reproducible installs, version
  guards, permissions, and distinguishing registry outage from missing version.

### 3. Large-catalog retrieval, measured before feature expansion

- [ ] Freeze a deterministic reference ranking and record baseline timings at
  multiple corpus sizes. Reuse `assay/`; separate build cost from query latency.
- [ ] Evaluate an inverted posting index and bounded top-k selection against the
  reference on ties, repeated terms, synonyms and random catalogs. Preserve ranking
  and ordering exactly. Add only if benchmarks justify memory and code cost.
- [ ] Introduce corpus revision-aware bounded resolution caching only if profiling
  shows repeated resolution is material. Never conflate this with provider KV cache
  or tool-result caching; never cache changing external tool results by text alone.
- [ ] Port proven algorithm changes to Rust/TypeScript with shared golden fixtures;
  retain independent versions and clearly document each package's scope.
- [ ] Evaluate held-out ToolRet retrieval tasks with lexical, dense and hybrid arms.
  Keep encoder dependencies in optional assay tooling, outside the core runtime.

### 4. Agent capability and execution design

- [ ] Specify a session API that retains conversation and offered schemas and records
  explicit discovery transitions. Existing `run()` is stateless and must stay compatible.
- [ ] Define executable discovery: a name/description tool result alone does not
  register a newly callable provider function. Test the entire discovery-to-call path.
- [ ] Specify caller-owned allowlists, argument validation, execution budgets,
  cancellation, approval for mutating tools, and observable failures before adding
  any automatic executor. Retrieval is not authorization.
- [ ] Design optional autonomous execution as a bounded loop using existing provider
  adapters. Verify real tool results and state changes, not just returned tool names.
- [ ] Test artifact generation as a real integration (create, validate, recover an
  artifact) using caller tools; do not introduce a generic artifact framework first.
- [ ] Make each accepted capability independently runnable and documented, then release.

### 5. Evidence and adoption

- [ ] Add durable per-query experiment records: commit, dataset hash, model version,
  parameters, arm order, errors, latency, token usage and outcomes.
- [ ] Evaluate tool arguments, abstention and end-to-end task success separately.
  Use repeated paired runs and query/session-level uncertainty estimates; do not
  count repeated outputs on one query as independent tasks.
- [ ] Model cache writes, reads, uncached input, TTL and task changes, then validate
  with observed usage. Compare all-tools, static subset and adaptive discovery.
- [ ] Publish reproducible results including regressions; correct the paper and site.
- [ ] Prepare one working developer example and a measurable adoption experiment.
  External outreach/messages require explicit authorization. Stars are not correctness.

## Verified research findings to preserve

- `run()` resolves each call; daemon forwards only the last message. No persistent
  resolve-once session exists in these paths.
- `find_more_tools()` returns names/descriptions, not executable registration or a loop.
- `assay/accuracy.py` checks only the first returned tool name, excludes no-tool gold
  queries, always runs naive first, prints aggregates, and omits the production escape hatch.
- Synonym expansion was tuned on observed fixture misses; those queries are development
  data, not an untouched generalization test. The scale set reuses them.
- PDF section IV-D claims a two-point change between runs 2/3, while Table IV gives
  72 to 84. Changed queries also prevent interpreting that difference as sampling noise.
- Equation 1 is conditional arithmetic, not proof that never rewriting is optimal.
- MCP SEP-1821 explicitly proposes a query parameter; calling all cited SEPs static
  is wrong. RAG-MCP and ToolRet belong in related work; When2Call concerns call/ask/abstain.
- Site calls the current full-scan resolver a zero-copy inverted index, equates tool
  count reduction with token reduction, and claims enforced session freezing.

Primary sources checked:
- https://arxiv.org/abs/2505.03275
- https://aclanthology.org/2025.naacl-long.174/
- https://github.com/mangopy/tool-retrieval-benchmark
- https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1821
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/

## Completion policy

Update this file at each meaningful checkpoint with commands and actual outcomes.
Unchecked work is not complete. A passed local suite is not an enterprise certification.
Do not infer successful publication from a tag or workflow start: inspect registry results.

## Additional audit findings, not yet fixed

Inspected: `server`, `_openai_wire`, `adapters`, `builtin`, `press`, `sandbox`,
`mcp_connect`, `config`, `credentials`, `_client_factory`, all provider adapters,
`providers`, `studio`, `studio_data`, and their relevant tests. CLI/wizard/setup
and the studio HTML still need a complete review. Reading is not verification.

- `press()` uses store length as a handle; removing an older entry can make a new
  write overwrite an existing payload. Add a deletion/reinsertion recovery test.
- Builtin `press.digest` discards its local recovery store and returns only text.
  Its promise of recoverability is false. Design caller-owned recovery explicitly.
- Tabular digest joins unescaped commas/newlines and can exceed `max_chars`.
- Server body parsing is outside exception handling, unbounded, and lacks timeout;
  exceptions expose raw messages. Stream false currently still returns SSE.
- Configured timeout/cost limits are parsed but not enforced. Make unsupported
  settings fail explicitly or implement and test enforcement before claiming support.
- Daemon drops preceding messages; do not silently call it a full chat proxy.
- Callable annotations under `from __future__ import annotations` are strings;
  current primitive type mapping can turn integer parameters into strings.
- Corpus permits duplicate names and mutable token/schema state. Decide compatibility
  and index revision semantics before adding cached resolution or execution.
- Gemini adapter assumes candidates exist; a prompt-blocked response can omit them.
- All native adapters retain only the last text block; test multi-block responses.
- MCP listing does not paginate. Installed SDK uses v2 snake_case fields and two
  transport streams; `mcp>=1` also permits older incompatible APIs. Test the supported
  version matrix before changing dependencies or normalizing wire data.
- No advanced retrieval or autonomous executor has been implemented in this checkpoint.

Review checkpoint: graph tools were invoked but reported targets not indexed; their
zero-impact result is not evidence. Caller search and regression tests were used.
Existing oversized modules are retained to avoid unrelated file churn; new regression
files are small. No new runtime dependencies were added.
