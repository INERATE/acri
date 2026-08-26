from types import SimpleNamespace

from acri import Ledger, Tool, index
from acri.daemon import RedactingLedger, default_ledger, handle_chat_completion


def _client(create_fn):
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create_fn)))


def test_handle_chat_completion_calls_the_real_acri_run():
    """docs/decisions.md: the daemon must be a thin wrapper, same resolve() as the
    library. Proof: a real tool call comes back shaped exactly like port.openai_compatible
    already produces it, because this handler calls acri.run(), not its own pipeline."""
    corpus = index([Tool(
        name="get_weather",
        description="Get the current weather for a city",
        parameters={"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    )])

    def create(**kwargs):
        assert kwargs["tools"][0]["function"]["name"] == "get_weather"
        call = SimpleNamespace(function=SimpleNamespace(name="get_weather", arguments='{"city": "Tokyo"}'))
        message = SimpleNamespace(content=None, tool_calls=[call])
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    request = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "what's the weather in Tokyo"}]}
    response = handle_chat_completion(request, corpus, _client(create), provider="openai", k=1)

    message = response["choices"][0]["message"]
    assert message["tool_calls"] == [{
        "id": "call_0", "type": "function",
        "function": {"name": "get_weather", "arguments": '{"city": "Tokyo"}'},
    }]


def test_handle_chat_completion_with_no_messages_is_an_empty_query():
    corpus = index([Tool(name="noop", description="does nothing")])
    client = _client(lambda **kw: SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="ok", tool_calls=None))]))
    response = handle_chat_completion({"messages": []}, corpus, client)
    assert response["choices"][0]["message"]["content"] == "ok"


def test_default_ledger_creates_the_dot_acri_directory(tmp_path):
    ledger = default_ledger(tmp_path / "sub" / "ledger.jsonl")
    assert isinstance(ledger, Ledger)
    assert (tmp_path / "sub").is_dir()


def test_redacting_ledger_never_writes_the_real_query(tmp_path):
    """decisions.md: conversation content is opt-in for the daemon. The real
    query must never reach disk through the default (redacted) path."""
    real = Ledger(tmp_path / "ledger.jsonl")
    redacting = RedactingLedger(real)
    redacting.record("this is a secret question", offered=[], selected=[], latency_ms=1.0)
    assert real.entries[0].query == "<redacted>"
    on_disk = (tmp_path / "ledger.jsonl").read_text(encoding="utf-8")
    assert "secret" not in on_disk
