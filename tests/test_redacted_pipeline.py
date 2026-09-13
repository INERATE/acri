from types import SimpleNamespace

from acri import Ledger, Tool, index
from acri.daemon import RedactingLedger, handle_chat_completion


def test_default_logging_preserves_metrics_without_recording_query(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ledger = Ledger(path)
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
        create=lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace(
            message=SimpleNamespace(content="ok", tool_calls=None))])
    )))
    response = handle_chat_completion(
        {"messages": [{"role": "user", "content": "private weather request"}]},
        index([Tool("weather", "Get weather")]), client,
        ledger=RedactingLedger(ledger),
    )
    assert response["choices"][0]["message"]["content"] == "ok"
    assert ledger.entries[0].corpus_size == 1
    assert ledger.entries[0].query == "<redacted>"
    assert "private weather request" not in path.read_text(encoding="utf-8")
