from types import SimpleNamespace

import acri
from acri import Tool, index
from acri.router import route


def test_cheap_model_wins_when_given():
    assert route("gpt-4o", "gpt-4o-mini") == "gpt-4o-mini"


def test_falls_through_to_model_when_no_cheap_tier_given():
    assert route("gpt-4o", None) == "gpt-4o"


def test_cheap_model_wins_even_with_no_explicit_model():
    assert route(None, "gpt-4o-mini") == "gpt-4o-mini"


def test_neither_given_is_none_so_the_provider_default_applies():
    assert route(None, None) is None


def _fake_openai_client(create_fn):
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create_fn)))


def test_run_routes_to_the_cheap_model_once_per_call():
    corpus = index([Tool(name="noop", description="does nothing")])
    seen_models = []

    def create(**kwargs):
        seen_models.append(kwargs["model"])
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="ok", tool_calls=None))])

    client = _fake_openai_client(create)
    acri.run("classify this", corpus, client, provider="openai", model="gpt-4o", cheap_model="gpt-4o-mini")
    acri.run("classify this", corpus, client, provider="openai", model="gpt-4o")
    assert seen_models == ["gpt-4o-mini", "gpt-4o"]


def test_a_strong_tier_retry_is_not_a_false_cache_hit_off_the_cheap_tier():
    """architecture.md #4.4: on failure, re-run the same unmodified query on the strong
    model. The two tiers must not share a cache entry, or the retry would just return the
    failed cheap-tier answer again."""
    corpus = index([Tool(name="noop", description="does nothing")])
    replies = iter(["cheap answer", "strong answer"])

    def create(**kwargs):
        text = next(replies)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text, tool_calls=None))])

    client = _fake_openai_client(create)
    cache = {}
    cheap = acri.run("classify this", corpus, client, model="gpt-4o", cheap_model="gpt-4o-mini", cache=cache)
    strong = acri.run("classify this", corpus, client, model="gpt-4o", cache=cache)
    assert cheap.text == "cheap answer"
    assert strong.text == "strong answer"
