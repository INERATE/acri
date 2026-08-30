from types import SimpleNamespace

import acri
from acri.corpus import Tool, index


def _weather_corpus():
    return index([Tool(name="get_weather", description="Get the current weather for a city")])


def _fake_client(create_fn):
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create_fn)))


def test_run_sends_query_as_the_prompt_when_prompt_is_omitted():
    def create(**kwargs):
        assert kwargs["messages"][0]["content"] == "what's the weather in Tokyo"
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="sunny", tool_calls=None))])

    acri.run("what's the weather in Tokyo", _weather_corpus(), _fake_client(create), provider="openai")


def test_run_sends_a_multimodal_prompt_while_resolving_on_the_text_query():
    image_prompt = [
        {"type": "text", "text": "what's the weather in this photo?"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}},
    ]

    def create(**kwargs):
        # the model gets the full multimodal content...
        assert kwargs["messages"][0]["content"] == image_prompt
        assert kwargs["tools"][0]["function"]["name"] == "get_weather"  # ...resolved from the text query
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="sunny", tool_calls=None))])

    acri.run(
        "what's the weather in this photo", _weather_corpus(), _fake_client(create),
        provider="openai", prompt=image_prompt,
    )


def test_run_with_an_explicit_prompt_bypasses_the_cache_even_when_one_is_given():
    """Two different images behind the same query text must never collide on one
    cache key -- a multimodal `prompt` opts out of caching entirely, on purpose."""
    calls = []

    def create(**kwargs):
        calls.append(kwargs["messages"][0]["content"])
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="ok", tool_calls=None))])

    client = _fake_client(create)
    cache = {}
    corpus = _weather_corpus()

    acri.run("describe this image", corpus, client, provider="openai", cache=cache, prompt=["image A"])
    acri.run("describe this image", corpus, client, provider="openai", cache=cache, prompt=["image B"])

    assert calls == [["image A"], ["image B"]]  # both went through -- neither was served from the other's cache entry
