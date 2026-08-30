from acri._wizard import interactive_setup


def test_declines_to_overwrite_an_existing_config(tmp_path, capsys):
    path = tmp_path / "acri.yaml"
    path.write_text("version: 1\n", encoding="utf-8")
    assert interactive_setup(path) == 0
    assert "already exists" in capsys.readouterr().out
    assert path.read_text(encoding="utf-8") == "version: 1\n"  # untouched


def test_refuses_to_run_non_interactively(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    path = tmp_path / "acri.yaml"
    assert interactive_setup(path) == 1
    assert "needs an interactive terminal" in capsys.readouterr().err
    assert not path.exists()


def _answer(*responses):
    it = iter(responses)
    return lambda prompt: next(it)


def test_writes_a_working_config_with_an_mcp_server(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", _answer(
        "gemini", "y", "github", "npx -y @modelcontextprotocol/server-github",
    ))
    monkeypatch.setenv("GEMINI_API_KEY", "x")
    path = tmp_path / "acri.yaml"

    assert interactive_setup(path) == 0

    from acri.config import from_yaml
    config = from_yaml(path)
    assert config.models.default == "gemini/gemini-2.5-flash"
    assert config.mcp[0].name == "github"
    assert config.mcp[0].command == ["npx", "-y", "@modelcontextprotocol/server-github"]
    assert "credentials look good" in capsys.readouterr().out


def test_openai_provider_picks_the_openai_default_model(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", _answer("openai", "n"))
    path = tmp_path / "acri.yaml"

    interactive_setup(path)

    from acri.config import from_yaml
    assert from_yaml(path).models.default == "openai/gpt-5.6-luna"


def test_anthropic_provider_picks_the_anthropic_default_model(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", _answer("anthropic", "n"))
    path = tmp_path / "acri.yaml"

    interactive_setup(path)

    from acri.config import from_yaml
    assert from_yaml(path).models.default == "anthropic/claude-sonnet-5"


def test_an_unknown_provider_falls_back_to_gemini(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", _answer("not-a-real-provider", "n"))
    path = tmp_path / "acri.yaml"

    interactive_setup(path)

    from acri.config import from_yaml
    assert from_yaml(path).models.default == "gemini/gemini-2.5-flash"


def test_skipping_the_mcp_server_still_writes_a_valid_config(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", _answer("gemini", "n"))
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    path = tmp_path / "acri.yaml"

    assert interactive_setup(path) == 0

    from acri.config import from_yaml
    assert from_yaml(path).mcp == []
    out = capsys.readouterr().out
    assert "no mcp: servers" in out
    assert "GEMINI_API_KEY" in out  # missing-credential report still ran
