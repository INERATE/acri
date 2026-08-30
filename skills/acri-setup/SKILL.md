---
name: acri-setup
description: Add acri (client-side tool resolution) to a project that calls an LLM with tools. Use when the user wants to install acri, cut their tool count before calling a model, or fix a "too many tools" / degraded tool-selection accuracy problem.
---

# Setting up acri

acri picks the few relevant tools from a larger catalog before you call a model — it
is a plain Python import, not a server, gateway, or framework. This skill sets it up
correctly in one pass: install, pick a provider, write a working `acri.yaml`, verify
credentials, wire it into existing code.

Full reference if anything here is unclear: `README.md` and `docs/architecture.md`
in [github.com/INERATE/acri](https://github.com/INERATE/acri).

## 1. Confirm this project actually needs it

acri earns its place once a tool catalog is large enough that a model starts picking
wrong — Anthropic's own docs put that cliff at 30–50 tools. If the project has fewer
than ~20 tools and no reported selection-accuracy problem, say so plainly and ask
before installing anything: acri adds a real dependency and a config file for a
problem that may not exist yet here.

## 2. Install

```bash
pip install pyacri
```

Only `acri`'s core (`corpus`, `compass`) is dependency-free. `acri.yaml` support needs
the `yaml` extra; `acri up`/`acri studio` need `server`/`studio`:

```bash
pip install "pyacri[yaml]"       # acri.yaml, acri init/check
pip install "pyacri[server]"     # acri up
pip install "pyacri[studio]"     # acri studio
```

## 3. Ask which provider, don't assume

Check the project's existing code/env first — an existing `OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`, an `openai.OpenAI(...)` call, etc. is a strong signal. If nothing
points at one provider, ask. Do not default silently to any single provider — acri
treats all of them equally. Full list with the exact `acri.yaml` line and required
env var for each: `README.md`, "Supported providers" table.

## 4. Write `acri.yaml`

Prefer `acri init` (writes a commented template you then edit) over hand-writing one
from scratch — run it, then fill in the picked provider:

```bash
acri init
```

The `models: default:` line takes `provider/model`, e.g. `anthropic/claude-sonnet-5`
or `ollama/qwen2.5-coder:32b` for a local server (no key needed there). If the project
has MCP servers already configured (check for an existing MCP client config), add them
under `mcp:` — same `name`/`command` or `name`/`url` shape as the tools it already
uses; do not invent a server that isn't actually there.

## 5. Verify credentials before touching any code

```bash
acri check acri.yaml
```

Prints exactly which env var is missing, if any. Fix those before step 6 — a
credential problem should surface here, not as a confusing runtime error later.

## 6. Wire it into the existing call site

Find where the project currently builds its tools list and calls the model. The
minimal integration is two lines around that call, nothing else in the codebase
changes:

```python
import acri

corpus = acri.index(existing_tools)   # build once, reuse across the whole task -- never per-turn
resolved = acri.resolve(query, corpus, k=5)
# hand `resolved` to whatever already calls the model, instead of the full tool list
```

Or let acri make the call too, if nothing provider-specific happens between resolving
and calling:

```python
result = acri.run(query, corpus, existing_client, provider="anthropic")
```

`provider` here is one of `acri.providers.PROVIDERS`' keys (same names as
`acri.yaml`'s prefix convention) — match whatever `existing_client` actually is.

**Do not** rebuild `corpus` inside a request handler or a loop — it is meant to be
built once (module load / app startup) and reused. Rebuilding it per-turn defeats the
entire point (`docs/decisions.md`'s caching argument) and is the single most common
mistake when wiring acri in.

## 7. What NOT to add

Do not build, suggest, or scaffold any of the following — each was deliberately cut,
with the reasoning in `docs/decisions.md`:
- Per-turn tool re-resolution ("optimizing" the list every message) — breaks prompt
  caching, costs more than it saves below a ~10x cut.
- Mid-conversation model switching, or picking among several models per task.
- Any inter-agent communication layer. acri resolves tools for one caller; it does
  not coordinate agents.

If the user asks for one of these specifically, tell them plainly why it's not part
of acri's design rather than working around this skill's guidance to build it anyway.

## 8. Done-state check

- `acri check acri.yaml` reports no missing credentials.
- The existing tool-calling code path now imports `acri` and calls `resolve()`/`run()`
  instead of sending the full tool list every time.
- `corpus = acri.index(...)` happens once, not per-request.
