from types import SimpleNamespace

from acri.compass import resolve
from acri.corpus import Tool, index
from acri.port import cached_call, gemini, openai_compatible
from acri.schemas import to_gemini_tools, to_openai_tools


def _resolved_weather_tool():
    corpus = index([Tool(
        name="get_weather",
        description="Get the current weather for a city",
        parameters={"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    )])
    return resolve("what's the weather in Tokyo", corpus, k=1)


def _fake_openai_client(create_fn):
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create_fn)))


def test_to_openai_tools_shapes_the_schema():
    tools = to_openai_tools(_resolved_weather_tool())
    assert tools == [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city",
            "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
        },
    }]


def test_openai_compatible_parses_a_tool_call():
    resolved = _resolved_weather_tool()

    def create(**kwargs):
        assert kwargs["tools"][0]["function"]["name"] == "get_weather"
        call = SimpleNamespace(function=SimpleNamespace(name="get_weather", arguments='{"city": "Tokyo"}'))
        message = SimpleNamespace(content=None, tool_calls=[call])
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    result = openai_compatible(_fake_openai_client(create), "what's the weather in Tokyo", resolved)
    assert result.tool_calls == [{"name": "get_weather", "arguments": '{"city": "Tokyo"}'}]
    assert result.text is None


def test_openai_compatible_parses_plain_text_with_no_tools_offered():
    def create(**kwargs):
        assert kwargs["tools"] is None
        message = SimpleNamespace(content="It's sunny.", tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    result = openai_compatible(_fake_openai_client(create), "hello", [])
    assert result.text == "It's sunny."
    assert result.tool_calls == []


def test_to_gemini_tools_shapes_the_schema():
    tools = to_gemini_tools(_resolved_weather_tool())
    assert tools == [{
        "name": "get_weather",
        "description": "Get the current weather for a city",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    }]


def test_gemini_parses_a_function_call():
    resolved = _resolved_weather_tool()

    def generate_content(**kwargs):
        assert kwargs["config"]["tools"][0]["function_declarations"][0]["name"] == "get_weather"
        part = SimpleNamespace(text=None, function_call=SimpleNamespace(name="get_weather", args={"city": "Tokyo"}))
        content = SimpleNamespace(parts=[part])
        return SimpleNamespace(candidates=[SimpleNamespace(content=content)])

    client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))
    result = gemini(client, "what's the weather in Tokyo", resolved)
    assert result.tool_calls == [{"name": "get_weather", "arguments": {"city": "Tokyo"}}]


def test_cached_call_skips_the_second_call_on_a_repeat_key():
    calls = []

    def call(x):
        calls.append(x)
        return f"result for {x}"

    cache = {}
    assert cached_call(call, cache, "k1", "a") == "result for a"
    assert cached_call(call, cache, "k1", "a") == "result for a"
    assert calls == ["a"]  # second call never reached `call`


def test_cached_call_with_no_cache_calls_every_time():
    calls = []

    def call(x):
        calls.append(x)
        return x

    cached_call(call, None, "k1", "a")
    cached_call(call, None, "k1", "a")
    assert calls == ["a", "a"]


def test_gemini_handles_a_blocked_response_without_crashing():
    resolved = _resolved_weather_tool()

    def generate_content(**kwargs):
        # A real shape: safety/recitation blocks and MAX_TOKENS-before-any-
        # content all leave candidate.content as None.
        return SimpleNamespace(candidates=[SimpleNamespace(content=None, finish_reason="SAFETY")])

    client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))
    result = gemini(client, "what's the weather in Tokyo", resolved)
    assert result.text is None
    assert result.tool_calls == []
