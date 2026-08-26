import pytest

from acri.adapters import from_callables, from_mcp_tools
from acri.corpus import Tool, index


def test_index_builds_from_tools():
    corpus = index([Tool(name="get_weather", description="Get the current weather for a city")])
    assert len(corpus) == 1
    assert corpus.tools[0].name == "get_weather"


def test_index_rejects_empty():
    with pytest.raises(ValueError):
        index([])


def test_from_mcp_tools_adapts_tools_list_response():
    mcp_response = [{
        "name": "get_pull_request",
        "description": "Fetch a PR",
        "inputSchema": {"type": "object", "properties": {"id": {"type": "integer"}}},
    }]
    tools = from_mcp_tools(mcp_response)
    assert tools[0].name == "get_pull_request"
    assert tools[0].parameters["properties"]["id"]["type"] == "integer"


def test_from_callables_derives_schema_from_signature():
    def get_weather(city: str, days: int = 1):
        """Get the weather forecast."""
        return f"{city} for {days} days"

    tool = from_callables([get_weather])[0]
    assert tool.name == "get_weather"
    assert tool.description == "Get the weather forecast."
    assert tool.parameters["properties"]["city"]["type"] == "string"
    assert tool.parameters["properties"]["days"]["type"] == "integer"
    assert tool.parameters["required"] == ["city"]
    assert tool.handler is get_weather
