import pytest

from acri.config import Config, McpEntry, from_yaml
from acri.credentials import missing_env_vars


def _write(tmp_path, text):
    path = tmp_path / "acri.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_from_yaml_parses_the_documented_example(tmp_path):
    path = _write(tmp_path, """
version: 1
models:
  default: gemini-2.5-flash
  cheap: gemini-2.5-flash-lite
mcp:
  - name: github
    command: ["npx", "-y", "@modelcontextprotocol/server-github"]
  - name: postgres
    url: http://localhost:3001
resolve:
  k: 3
limits:
  timeout_ms: 5000
  max_cost_per_task_usd: 0.05
""")
    config = from_yaml(path)
    assert config.models.default == "gemini-2.5-flash"
    assert config.models.cheap == "gemini-2.5-flash-lite"
    assert config.mcp == [
        McpEntry(name="github", command=["npx", "-y", "@modelcontextprotocol/server-github"], url=None),
        McpEntry(name="postgres", command=None, url="http://localhost:3001"),
    ]
    assert config.k == 3
    assert config.limits.timeout_ms == 5000
    assert config.limits.max_cost_per_task_usd == 0.05


def test_from_yaml_defaults_are_sensible(tmp_path):
    config = from_yaml(_write(tmp_path, "version: 1\n"))
    assert config == Config(version=1)


def test_from_yaml_rejects_an_unsupported_version(tmp_path):
    with pytest.raises(ValueError):
        from_yaml(_write(tmp_path, "version: 2\n"))


def test_from_yaml_rejects_an_mcp_entry_with_neither_command_nor_url(tmp_path):
    with pytest.raises(ValueError):
        from_yaml(_write(tmp_path, "version: 1\nmcp:\n  - name: broken\n"))


def test_from_yaml_rejects_an_mcp_entry_with_both_command_and_url(tmp_path):
    text = 'version: 1\nmcp:\n  - name: broken\n    command: ["x"]\n    url: http://localhost:1\n'
    with pytest.raises(ValueError):
        from_yaml(_write(tmp_path, text))


def test_from_yaml_parses_a_sandboxed_mcp_entry(tmp_path):
    text = ('version: 1\nmcp:\n  - name: untrusted\n    command: ["npx", "-y", "some-server"]\n'
            '    sandbox:\n      image: node:20-slim\n      network: false\n')
    config = from_yaml(_write(tmp_path, text))
    sandbox = config.mcp[0].sandbox
    assert sandbox.image == "node:20-slim"
    assert sandbox.network is False
    assert sandbox.memory == "256m"  # unset fields keep SandboxConfig's own defaults


def test_from_yaml_rejects_sandbox_on_a_url_entry(tmp_path):
    text = 'version: 1\nmcp:\n  - name: broken\n    url: http://localhost:1\n    sandbox:\n      image: x\n'
    with pytest.raises(ValueError):
        from_yaml(_write(tmp_path, text))


def test_missing_env_vars_reports_what_is_actually_missing(tmp_path, monkeypatch):
    path = _write(tmp_path, "version: 1\nmodels:\n  default: gemini-2.5-flash\n  cheap: gpt-4o-mini\n")
    config = from_yaml(path)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert missing_env_vars(config) == ["GEMINI_API_KEY", "OPENAI_API_KEY"]

    monkeypatch.setenv("GEMINI_API_KEY", "x")
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    assert missing_env_vars(config) == []
