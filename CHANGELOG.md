# Changelog

Prior releases (v0.3.0–v0.4.3) are tracked in git tags and their release commit
messages, not backfilled here. This file starts at v0.5.0.

## [0.6.0]

### Added
- Multimodal passthrough: `acri.run(..., prompt=[...])` sends a caller-built,
  provider-shaped content list (image/audio) to the model while `query` stays
  plain text for tool resolution. Fixed a real bug found while building this:
  `port_bedrock.py` always wrapped `prompt` in `{"text": prompt}}`, so a list
  would have nested wrong; the other three ports needed no change; each
  provider's own `content` field already accepts a string or a block list.
  `acri up`'s HTTP handler (`daemon.py`) extracts just the text portion of an
  incoming OpenAI-shaped multimodal request for resolution, and forwards the
  full content unchanged. A multimodal `prompt` bypasses `cache` automatically
  — two different images behind the same query text must never share a key.
- `acri.press`/`acri.recover`/`acri.Pressed` now reachable from the top-level
  package, not just `acri.press.press()` — a real gap surfaced while testing
  the resolve→run→press→resolve→run multi-phase pattern end to end.
- Multi-provider support: Anthropic (direct), AWS Bedrock, Cloudflare Workers AI,
  OpenRouter, NVIDIA NIM, Grok, and local servers (Ollama, vLLM, LM Studio) — 12
  providers total, none "native." One canonical `acri.providers.PROVIDERS` registry
  replaces three copies that could drift (`run()`, `assay/accuracy.py`, `server.py`).
- `acri.yaml`'s `models: default:`/`cheap:` accepts explicit `provider/model`
  (e.g. `anthropic/claude-sonnet-5`), alongside the original bare-name inference
  for gemini/openai, unchanged for existing configs.
- New native adapters `acri/port_anthropic.py`, `acri/port_bedrock.py` (joining
  `port_gemini.py`, split out of `port.py` one-per-file). Every OpenAI-compatible
  provider reuses `port.openai_compatible()` unchanged — no new port code.
- `acri/_client_factory.py` (production, `acri up`) and `assay/clients.py` (the
  benchmark script) both build clients from the same table.
- `acri/credentials.py` asserts its env-var table matches `PROVIDERS` at import
  time — a provider added to one and forgotten in the other fails immediately.
- `acri setup`'s wizard now offers all 12 providers, not just gemini/openai.

### Fixed
- `config.models.cheap` flowed to an SDK call unstripped of any `provider/` prefix
  — a real bug, found while tracing the new convention through `server.py`.
- Documentation no longer implies gemini/openai are first-class — every provider
  gets equal treatment, an explicit `provider/model` example, and its own env vars.
- Model version defaults were 8 months stale (from an unrelated project's
  January-2026 config, copied without checking): `claude-sonnet-4-6` →
  `claude-sonnet-5`, `gpt-4o-mini` → `gpt-5.6-luna`, `grok-4` → `grok-4.6`.
  Verified against each provider's own current docs, not assumed.
  `gemini-2.5-flash` was checked too and kept — still live, not deprecated.

### Docs
- README: new "Supported providers" table, one row per provider with a working
  `acri.yaml` line and required env vars.
- `docs/decisions.md`: new "One provider registry, not three that can drift" section.
- `docs/research/sections/03a-architecture.tex`: the paper's own architecture
  description updated to name every provider port now actually supports (the
  accuracy claim itself is unchanged — still `gemini-2.5-flash` only, stated
  explicitly right next to the provider list so the two can't be conflated).
- `CONTRIBUTING.md`: the "run CI's checks locally" step now gives the actual
  runnable commands instead of pointing at the workflow file.

### Tests
- 131 passing Python tests (was 103; +28 for the 12-provider registry, the new
  native adapters, `credentials.py`'s expanded parsing, and multimodal passthrough).
- Verified CI needs no new dependencies: ran the full suite in a clean venv with
  only the `dev` extra installed (no boto3/anthropic/openai) — every new module's
  SDK import is function-scoped, never at module level. 9/9 Rust, 5/5 TypeScript,
  unaffected (they port `corpus`+`compass` only, never touch provider adapters).

## [0.5.0]

### Added
- `acri/builtin.py` — first-party tool registry shipping `press.digest`
  (compacts a large result via `press.press`, dropping nothing unrecoverably).
  `sandbox.run` was considered and rejected: sandbox config isn't a tool in the
  MCP sense. See `docs/research/future-work-tool-pack.md` for the original scoping.
- Opt-in `tools.builtin: [press.digest]` schema in `acri.yaml`. Empty by default;
  `acri up` loads the named tools into the same corpus as `mcp:` entries.
- Automatic load-time schema validation in `config.py` — an unknown `builtin:`
  name raises `ValueError` at config-load time, same as a malformed `mcp:` entry.

### Docs
- `docs/decisions.md` — new "The builtin tool pack" section.
- `docs/research/future-work-tool-pack.md` — flipped from planned to built.

### Tests
- 103 passing Python tests (was 97 before this release; +6 for `acri/builtin.py`
  and the new `config.py` parsing).
- 117 passing across the full multi-language suite: 103 Python + 9 Rust
  (`cargo test`) + 5 TypeScript (`npm test`). The Rust/TS counts are unaffected
  by this release — checked, not assumed.
