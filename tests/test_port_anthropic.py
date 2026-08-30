from types import SimpleNamespace

from acri.compass import resolve
from acri.corpus import Tool, index
from acri.port_anthropic import anthropic


def _resolved_weather_tool():
    corpus = index([Tool(
        name="get_weather",
        description="Get the current weather for a city",
        parameters={"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    )])
    return resolve("what's the weather in Tokyo", corpus, k=1)


def _fake_anthropic_client(create_fn):
    return SimpleNamespace(messages=SimpleNamespace(create=create_fn))


def test_anthropic_parses_a_tool_use_block():
    resolved = _resolved_weather_tool()

    def create(**kwargs):
        assert kwargs["tools"][0]["name"] == "get_weather"
        assert kwargs["max_tokens"] == 1024  # the required-by-the-API default
        block = SimpleNamespace(type="tool_use", name="get_weather", input={"city": "Tokyo"})
        return SimpleNamespace(content=[block])

    result = anthropic(_fake_anthropic_client(create), "what's the weather in Tokyo", resolved)
    assert result.tool_calls == [{"name": "get_weather", "arguments": {"city": "Tokyo"}}]
    assert result.text is None


def test_anthropic_parses_plain_text_with_no_tools_offered():
    def create(**kwargs):
        assert kwargs["tools"] == []
        block = SimpleNamespace(type="text", text="It's sunny.")
        return SimpleNamespace(content=[block])

    result = anthropic(_fake_anthropic_client(create), "hello", [])
    assert result.text == "It's sunny."
    assert result.tool_calls == []


def test_anthropic_handles_a_max_tokens_stop_without_crashing():
    def create(**kwargs):
        # A real shape: hitting max_tokens before any content block is possible.
        return SimpleNamespace(content=[])

    result = anthropic(_fake_anthropic_client(create), "hello", [])
    assert result.text is None
    assert result.tool_calls == []


def test_anthropic_respects_a_custom_max_tokens():
    def create(**kwargs):
        assert kwargs["max_tokens"] == 4096
        return SimpleNamespace(content=[])

    anthropic(_fake_anthropic_client(create), "hello", [], max_tokens=4096)
