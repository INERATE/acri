from acri._setup import ensure_config, run_safely


def test_ensure_config_returns_none_when_the_file_exists(tmp_path):
    path = tmp_path / "acri.yaml"
    path.write_text("version: 1\n", encoding="utf-8")
    assert ensure_config(path) is None


def test_ensure_config_prints_a_friendly_message_when_non_interactive(tmp_path, monkeypatch, capsys):
    """A daemon supervisor's stdin isn't a tty -- must never block on input()."""
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    path = tmp_path / "acri.yaml"
    assert ensure_config(path) == 1
    assert "run `acri init` first" in capsys.readouterr().err
    assert not path.exists()  # nothing was auto-created without a yes


def test_ensure_config_writes_the_template_on_an_interactive_yes(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    path = tmp_path / "acri.yaml"
    assert ensure_config(path) == 1  # still can't proceed -- needs real mcp:/models: values
    assert path.exists()
    assert "version: 1" in path.read_text(encoding="utf-8")
    assert "then rerun" in capsys.readouterr().out


def test_ensure_config_declines_on_an_interactive_no(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    path = tmp_path / "acri.yaml"
    assert ensure_config(path) == 1
    assert not path.exists()


def test_run_safely_returns_1_and_prints_the_error_instead_of_raising(capsys):
    def boom():
        raise ValueError("no mcp: servers configured")

    assert run_safely("acri up", boom) == 1
    assert "acri up: no mcp: servers configured" in capsys.readouterr().err


def test_run_safely_returns_0_and_passes_args_through_on_success():
    calls = []
    assert run_safely("label", lambda a, b=None: calls.append((a, b)), "x", b="y") == 0
    assert calls == [("x", "y")]
