# Changelog

Prior releases (v0.3.0–v0.4.3) are tracked in git tags and their release commit
messages, not backfilled here. This file starts at v0.5.0.

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
