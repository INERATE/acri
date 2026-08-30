# Contributing to acri

acri is a small, sharp library that refuses to grow into a framework. Contributions are
held to that standard — the constraint is the product.

## Ground rules

1. **Laziest thing that works.** No abstraction with one implementation. No dependency
   for what twenty lines do. Standard library first, then an already-installed dep, then
   new code. The shortest working diff wins.
2. **No unreproducible numbers.** No performance claim enters this repository without a
   script in `assay/` that regenerates it and a committed run. This rule has no
   exceptions, and it applies to READMEs, docs, issues, and commit messages.
3. **The resolver may be wrong; it may never be silently wrong.** Every decision acri
   makes is recorded in `ledger`. A tool that was considered and skipped is as important
   to log as one that was chosen.
4. **`gate` is advisory, never authoritative.** A false "no tool needed" makes a model
   answer from memory — confident, fluent, wrong, with no error and no retry. Nothing in
   acri may suppress a tool call the model actually wanted to make.
5. **Append-only by default.** Anything that rewrites a prompt prefix invalidates the
   provider's cache and costs the user money. If a change rewrites history, it must show
   the arithmetic proving it wins.
6. **No daemon, no gateway, no port.** acri is an import. A change that requires the user
   to run a process is out of scope by definition.
7. **Code files stay small** — 250 words, 350 hard cap. Docs are exempt.

## What to contribute

| Surface | What it looks like |
|---------|--------------------|
| **`port` adapters** | A new provider in ~50 lines: take tools + query, return the request payload that provider expects. Highest-value contribution. |
| **`corpus` ingesters** | Teach acri to read a new tool source (OpenAPI, a registry format, a framework's tool objects). |
| **`assay` benchmarks** | A reproducible scenario with a committed run. Benchmarks that *disprove* something are more valuable than ones that confirm it. |
| **`compass` retrieval** | Better ranking. Must come with an `assay` run showing it beats the current default. |
| **Docs** | Especially corrections. The architecture doc names its own weak points; sharpening them is welcome. |

## Workflow

1. Open an issue first for anything non-trivial — a template is provided. Small fixes can
   go straight to a PR.
2. Fork, branch (`feat/<slug>` or `fix/<slug>`).
3. Run the same checks CI runs, before you push — CI runs nothing beyond this:
   ```bash
   pip install -e ".[dev]"
   pytest -q
   ```
   That's the whole gate for `port`/`corpus`/`compass`/config changes — no provider SDK
   needed even for a new `port_*.py` adapter, since every adapter takes a duck-typed
   client (fakes in the test, real SDK only at actual call time). Touching `docs/`,
   `README.md`, or any `.svg`/`.html`: also see the claims-policy script in
   `.github/workflows/ci.yml` — no unreceipted `%`/`x faster` claim survives it.
4. PR describing what it does, **why it is the minimal version**, and what you
   deliberately did not build.
5. One maintainer review plus green CI merges it.

## Commit style

Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`). Subjects under 72 characters.

## Disagreeing with the design

The architecture doc is an argument, not a decree. If you think a layer is wrong, open an
issue titled `design:` and make the case. Several parts of acri exist specifically because
an earlier version of the design was wrong and someone said so.

## Questions

Open a discussion or an issue. Be kind — see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
