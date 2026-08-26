# acri-core (Rust)

A minimal, faithful Rust port of acri's v0.1 resolver: `Tool`/`Corpus`/`index()` and
BM25 `resolve()`, plus their two small dependencies (tokenize, query-alias expansion).
Nothing else — no `port`, `daemon`, `server`, `cli`, `config`, `gate`, `press`,
`sandbox`, `ledger`, `router`, or `escape_hatch`. Zero external dependencies.

## This ships ahead of its own gate — stated plainly, not glossed over

`docs/decisions.md` (the Python project's own design doc) is explicit about when a
Rust port is warranted:

> **Rust / C++** | Only if `assay` shows Python ranking is a measurable share of a
> turn. Against a network call that dominates it, that is close to arithmetically
> impossible.

That condition hasn't just gone unmet — it's been measured and answered *no*.
`assay/scale.py` (500-tool corpus) measured Python `compass.resolve()` at
**p50 0.179ms, p95 0.285ms**. A real LLM call runs hundreds of milliseconds to
several seconds. Resolution is not a measurable share of a turn.

This crate exists anyway, built at the maintainer's explicit request — the same
override pattern used elsewhere in this project this session (`gate`, `press`,
`sandbox`, and the `acri up` daemon all shipped ahead of their own gates too, each
one stated in its own README row). Treat this as a proof that the port is viable,
not as a performance fix for a problem the Python numbers say doesn't exist.

## Status

9/9 tests passing (`cargo test`): 4 unit tests alongside `tokenize`/`expand`/`index`,
5 integration tests in `tests/resolve.rs` mirroring the Python project's
`tests/test_compass.py` case-for-case — same fixture, same queries — so behavior
parity is verified, not assumed.
