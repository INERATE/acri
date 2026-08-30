# Cookbook: real, verified patterns

Every example on this page was actually run against `acri.run()` with a fake client
before being written down — not narrated from what the API is supposed to do. `python -c`
one-liners are in the commit that added this file if you want to re-run them yourself.

## Multi-phase provider handoff (research on one model, write-up on another)

This is the pattern people usually mean by "route between models" — and it's fully
supported today, because it's just two independent `acri.run()` calls. **Your code decides
the handoff; acri never switches providers mid-task on its own** (`docs/decisions.md`
explains why that's a deliberate boundary, not a gap).

```python
import acri
from acri.press import press

corpus = acri.index([
    acri.Tool(name="search_pricing_docs", description="search competitor pricing documents"),
    acri.Tool(name="draft_proposal", description="draft an executive proposal document"),
])

# Phase 1: fast/cheap model does the research
research = acri.run(
    "search competitor pricing documents", corpus, my_gemini_client,
    provider="gemini", model="gemini-2.5-flash",
)

# Compress before handing off -- keeps phase 2's prompt small and cache-stable,
# instead of carrying phase 1's full raw output into a second model's context.
digest = press(research.text, store={}).digest

# Phase 2: a different provider entirely, its own fresh resolve + its own cache key
final = acri.run(
    f"Draft a proposal based on: {digest}", corpus, my_anthropic_client,
    provider="anthropic", model="claude-sonnet-5",
)
```

Each `acri.run()` call resolves tools fresh against its own corpus and gets its own cache
key (`provider`, `model`, and `query` are all part of it) — nothing from phase 1 leaks into
phase 2's cache entry, and nothing about this requires acri to know phases exist at all.

## Multimodal (image/audio alongside the query)

`query` stays plain text — it's what resolves tools. `prompt` carries whatever you actually
want the model to see, in that provider's own content-block shape:

```python
result = acri.run(
    "what's the weather in this photo",  # resolves tools on this
    corpus, my_gemini_client, provider="gemini",
    prompt=[
        {"text": "what's the weather in this photo?"},
        {"inline_data": {"mime_type": "image/jpeg", "data": base64_image}},
    ],
)
```

A multimodal `prompt` bypasses `cache` automatically if you pass one — two different images
behind the same query text must never collide on one cache key.

## Cheap/strong tier routing (one call, chosen once, before generating)

```python
result = acri.run(
    "classify this document", corpus, my_openai_client, provider="openai",
    model="gpt-5.6-sol",       # the strong tier, if this call needed it
    cheap_model="gpt-5.6-luna", # used instead, since this call is stateless/prefix-free
)
```

`cheap_model`, when given, always wins for that one call — it's not a fallback path or a
retry, it's the caller's own eligibility judgment (`docs/architecture.md` §4.4: stateless,
prefix-free calls only — classification, extraction, summarizing a tool result). Never use
this to swap models mid-conversation; that's the exact case decisions.md documents as
measurably harmful ([arXiv:2603.03111](https://arxiv.org/abs/2603.03111)).

## What none of this is

No pattern above has acri choosing a provider on its own, executing a tool, generating
content (an image, a video, a Blender scene), or coordinating more than one agent. It
resolves tools for one caller, one call at a time. The workflow — including which model
runs when — is always your code's decision.
