# acri-core (TypeScript)

A minimal TypeScript port of acri's core resolver: `Tool`/`Corpus`/`index()` and
BM25 `resolve()` — the v0.1 scope `docs/decisions.md` (the Python repo's own
design doc) calls "a complete product on its own." Nothing else is ported: no
port/daemon/server/cli/config/gate/press/sandbox/ledger/router/adapters/
escape-hatch.

Mirrors the Python implementation's behavior directly, not just its shape:
same BM25 constants (`K1=1.5`, `B=0.75`), same tokenizer (lowercase, strip
`'`/`'`, `[a-z0-9]+`, the same stopword list), same query-only synonym
expansion (never applied to indexed tool text — see `src/synonyms.ts`'s
comment for why that matters), same `resolve()` semantics: zero-score tools
are dropped rather than padded in, the top score normalizes to 1.0, `k` is
respected. `test/compass.test.ts` mirrors `tests/test_compass.py`'s five
cases exactly, same fixture and queries, and passes.

## Shipped ahead of its own gate

`docs/decisions.md`:

> **TypeScript** | A real gap, and the JavaScript agent ecosystem is large.
> Port after the Python package has users, never in parallel with it.

That condition is not met — there is no PyPI release with real users yet
([`.github/workflows/publish.yml`](../.github/workflows/publish.yml) exists
but hasn't been triggered). Shipping this now is exactly the scenario that
line warns against: it doubles the maintenance surface for every future acri
feature before anything has shown someone actually wants the TypeScript side.
Built anyway at the maintainer's explicit request — the same override pattern
used elsewhere in this project (`gate`, `press`, `sandbox`, and the `daemon`
all shipped ahead of their own gates too; see the root
[`README.md`](../README.md)'s Roadmap table). Stated here plainly, not
softened, so this isn't mistaken for a maintained, gate-cleared parallel
implementation — it's a v0.1-equivalent skeleton, nothing more.

## Run

```
npm install
npm test
```
