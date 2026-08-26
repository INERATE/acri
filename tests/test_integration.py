from types import SimpleNamespace

import pytest

import acri
from acri import Ledger, Tool, index


def test_end_to_end_openai_pipeline_logs_to_ledger():
    """prompt -> compass.resolve -> port.openai_compatible -> ledger.record, no mock gaps in between."""
    corpus = index([
        Tool(
            name="get_weather",
            description="Get the current weather for a city",
            parameters={"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
        ),
        Tool(name="get_stock_price", description="Get the current stock price for a ticker symbol"),
    ])

    def create(**kwargs):
        assert kwargs["tools"][0]["function"]["name"] == "get_weather"
        call = SimpleNamespace(function=SimpleNamespace(name="get_weather", arguments='{"city": "Tokyo"}'))
        message = SimpleNamespace(content=None, tool_calls=[call])
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    ledger = Ledger()

    result = acri.run("what's the weather in Tokyo", corpus, client, provider="openai", k=1, ledger=ledger)

    assert result.tool_calls == [{"name": "get_weather", "arguments": '{"city": "Tokyo"}'}]
    assert len(ledger.entries) == 1
    entry = ledger.entries[0]
    assert entry.query == "what's the weather in Tokyo"
    assert entry.offered == ["get_weather"]
    assert entry.selected == ["get_weather"]
    assert entry.latency_ms >= 0


def test_run_without_a_ledger_still_works():
    corpus = index([Tool(name="noop", description="does nothing")])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
        create=lambda **kw: SimpleNamespace(choices=[SimpleNamespace(
            message=SimpleNamespace(content="ok", tool_calls=None))]),
    )))
    result = acri.run("hello", corpus, client, provider="openai")
    assert result.text == "ok"


def test_run_with_a_cache_skips_a_repeated_call():
    corpus = index([Tool(name="noop", description="does nothing")])
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="ok", tool_calls=None))])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    cache = {}

    acri.run("hello", corpus, client, provider="openai", cache=cache)
    acri.run("hello", corpus, client, provider="openai", cache=cache)
    assert len(calls) == 1  # second run() was an exact-match cache hit

    acri.run("something else", corpus, client, provider="openai", cache=cache)
    assert len(calls) == 2  # a different query is not the same request -- no false hit


def test_run_rejects_an_unknown_provider():
    corpus = index([Tool(name="noop", description="does nothing")])
    with pytest.raises(ValueError):
        acri.run("hello", corpus, client=object(), provider="not-a-provider")
