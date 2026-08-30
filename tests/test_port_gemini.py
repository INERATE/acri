from types import SimpleNamespace

from acri.compass import resolve
from acri.corpus import Tool, index
from acri.port_gemini import gemini


def _resolved_weather_tool():
    corpus = index([Tool(
        name="get_weather",
        description="Get the current weather for a city",
        parameters={"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    )])
    return resolve("what's the weather in Tokyo", corpus, k=1)


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
