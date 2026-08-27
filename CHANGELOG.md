# Changelog

Prior releases (v0.3.0–v0.4.3) are tracked in git tags and their release commit
messages, not backfilled here. This file starts at v0.5.0.

## [0.5.0]

### Added
- `acri/builtin.py` — a first-party tool registry. Ships one tool, `press.digest`
  (compacts a large result via `press.press`, dropping nothing unrecoverably).
  `sandbox.run` was considered and rejected: sandbox config isn't a tool in the
  MCP sense. See `docs/research/future-work-tool-pack.md` for the original scoping.
- `tools: builtin: [...]` in `acri.yaml` — opt-in only, empty by default. `acri up`
  loads the named tools into the same corpus as `mcp:` entries. An unknown name
  raises `ValueError` at config-load time, same as a malformed `mcp:` entry.

### Docs
- `docs/decisions.md` — new "The builtin tool pack" section.
- `docs/research/future-work-tool-pack.md` — flipped from planned to built.

### Tests
- 103/103 Python tests passing (was 97 before this release; +6 for
  `acri/builtin.py` and the new `config.py` parsing).
- Rust core: 9/9 (`cargo test`). TypeScript SDK: 5/5 (`npm test`). Unaffected by
  this release — checked, not assumed.
