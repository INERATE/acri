from acri.compass import resolve
from acri.corpus import Tool, index
from acri.schemas import to_gemini_tools, to_openai_tools


def _resolved_weather_tool():
    corpus = index([Tool(
        name="get_weather",
        description="Get the current weather for a city",
        parameters={"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    )])
    return resolve("what's the weather in Tokyo", corpus, k=1)


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


def test_to_gemini_tools_shapes_the_schema():
    tools = to_gemini_tools(_resolved_weather_tool())
    assert tools == [{
        "name": "get_weather",
        "description": "Get the current weather for a city",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    }]


def test_to_gemini_tools_strips_schema_dialect_key():
    """A real MCP server's inputSchema commonly self-declares $schema (e.g.
    @modelcontextprotocol/server-filesystem does). Gemini's pydantic-validated
    function-calling schema rejects unknown keys -- found live, not guessed."""
    corpus = index([Tool(
        name="read_file", description="Read a file",
        parameters={"$schema": "http://json-schema.org/draft-07/schema#", "type": "object", "properties": {}},
    )])
    tools = to_gemini_tools(resolve("read a file", corpus, k=1))
    assert "$schema" not in tools[0]["parameters"]
    assert tools[0]["parameters"] == {"type": "object", "properties": {}}
