from types import SimpleNamespace

from acri.compass import resolve
from acri.corpus import Tool, index
from acri.port_bedrock import bedrock


def _resolved_weather_tool():
    corpus = index([Tool(
        name="get_weather",
        description="Get the current weather for a city",
        parameters={"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    )])
    return resolve("what's the weather in Tokyo", corpus, k=1)


def _fake_bedrock_client(converse_fn):
    return SimpleNamespace(converse=converse_fn)


def test_bedrock_parses_a_tool_use_block():
    resolved = _resolved_weather_tool()

    def converse(**kwargs):
        assert kwargs["toolConfig"]["tools"][0]["toolSpec"]["name"] == "get_weather"
        return {"output": {"message": {"content": [
            {"toolUse": {"toolUseId": "t1", "name": "get_weather", "input": {"city": "Tokyo"}}},
        ]}}}

    result = bedrock(_fake_bedrock_client(converse), "what's the weather in Tokyo", resolved)
    assert result.tool_calls == [{"name": "get_weather", "arguments": {"city": "Tokyo"}}]
    assert result.text is None


def test_bedrock_parses_plain_text_with_no_tools_offered():
    def converse(**kwargs):
        assert "toolConfig" not in kwargs
        return {"output": {"message": {"content": [{"text": "It's sunny."}]}}}

    result = bedrock(_fake_bedrock_client(converse), "hello", [])
    assert result.text == "It's sunny."
    assert result.tool_calls == []


def test_bedrock_handles_a_guardrail_block_without_crashing():
    def converse(**kwargs):
        # A real shape: a guardrail intervention can leave "message" absent entirely.
        return {"output": {}, "stopReason": "content_filtered"}

    result = bedrock(_fake_bedrock_client(converse), "hello", [])
    assert result.text is None
    assert result.tool_calls == []
