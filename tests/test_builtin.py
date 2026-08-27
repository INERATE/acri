import pytest

from acri.builtin import resolve_builtin


def test_resolve_builtin_returns_known_tools_in_order():
    tools = resolve_builtin(["press.digest"])
    assert [t.name for t in tools] == ["press.digest"]


def test_resolve_builtin_empty_list_opts_out_of_everything():
    assert resolve_builtin([]) == []


def test_resolve_builtin_rejects_an_unknown_name():
    with pytest.raises(ValueError):
        resolve_builtin(["not.a.real.tool"])


def test_press_digest_handler_compacts_a_large_result():
    tool = resolve_builtin(["press.digest"])[0]
    big = [{"id": i} for i in range(50)]
    digest = tool.handler(big, max_chars=10, max_rows=5)
    assert "more rows" in digest
