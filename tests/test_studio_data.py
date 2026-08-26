import json

from acri.config import Config, McpEntry, ModelsConfig, SandboxConfig
from acri.studio_data import read_ledger, recent, topology


def _write_ledger(tmp_path, entries):
    path = tmp_path / "ledger.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
    return path


def test_read_ledger_returns_empty_list_when_the_file_does_not_exist(tmp_path):
    assert read_ledger(tmp_path / "missing.jsonl") == []


def test_read_ledger_parses_each_line(tmp_path):
    path = _write_ledger(tmp_path, [{"query": "a"}, {"query": "b"}])
    assert read_ledger(path) == [{"query": "a"}, {"query": "b"}]


def test_topology_reads_servers_and_models_from_config(tmp_path):
    config = Config(
        version=1,
        models=ModelsConfig(default="gemini-2.5-flash", cheap="gemini-2.5-flash-lite"),
        mcp=[
            McpEntry(name="github", command=["npx", "-y", "server-github"]),
            McpEntry(name="untrusted", command=["npx", "-y", "server-fs"], sandbox=SandboxConfig(image="node:20-slim")),
            McpEntry(name="postgres", url="http://localhost:3001"),
        ],
    )
    result = topology(config, tmp_path / "missing.jsonl")
    assert result["models"] == {"default": "gemini-2.5-flash", "cheap": "gemini-2.5-flash-lite"}
    assert result["servers"] == [
        {"name": "github", "target": "npx", "sandboxed": False},
        {"name": "untrusted", "target": "npx", "sandboxed": True},
        {"name": "postgres", "target": "http://localhost:3001", "sandboxed": False},
    ]
    assert result["tools"] == []  # no ledger history yet


def test_topology_infers_tool_server_from_name_prefix_and_counts_repeats(tmp_path):
    path = _write_ledger(tmp_path, [
        {"offered": ["github_merge_pull_request", "postgres_query"]},
        {"offered": ["github_merge_pull_request"]},
    ])
    result = topology(Config(version=1), path)
    tools = {t["name"]: t for t in result["tools"]}
    assert tools["github_merge_pull_request"] == {"name": "github_merge_pull_request", "server": "github", "seen": 2}
    assert tools["postgres_query"]["seen"] == 1


def test_recent_returns_newest_first_and_respects_limit(tmp_path):
    path = _write_ledger(tmp_path, [{"query": "first"}, {"query": "second"}, {"query": "third"}])
    assert recent(path, limit=2) == [{"query": "third"}, {"query": "second"}]
