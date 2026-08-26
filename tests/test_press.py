from acri.press import Pressed, press, recover


def test_small_results_pass_through_unpressed():
    store = {}
    result = press({"id": 1, "name": "small"}, store)
    assert result.handle is None
    assert store == {}


def test_large_uniform_table_gets_a_toon_style_digest():
    rows = [{"id": i, "email": f"user{i}@acme.com"} for i in range(50)]
    store = {}
    result = press(rows, store, max_rows=5, max_chars=100)
    assert isinstance(result, Pressed)
    assert result.handle is not None
    assert "id,email" in result.digest  # header once, not per row
    assert "45 more rows" in result.digest
    assert len(result.digest) < result.full_chars  # actually smaller, not just reshaped


def test_recover_returns_exactly_what_was_pressed():
    """The fidelity promise: nothing press drops is gone."""
    rows = [{"id": i} for i in range(50)]
    store = {}
    pressed = press(rows, store, max_rows=5, max_chars=50)
    assert recover(pressed.handle, store) == rows


def test_large_non_uniform_result_still_gets_a_handle():
    value = {"nested": {"a": list(range(200))}}
    store = {}
    pressed = press(value, store, max_chars=50)
    assert pressed.handle is not None
    assert recover(pressed.handle, store) == value
