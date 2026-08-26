"""_wizard — `acri setup`: a guided flow, not just a static template.

Provider, then one optional MCP server, written straight to a working
acri.yaml, checked for credentials immediately -- vs. `acri init`, which
writes a template you then hand-edit. Never runs non-interactively (same
reasoning as _setup.ensure_config): a Y/N-driven flow with no terminal
attached just hangs forever waiting for input that never comes.
"""
from __future__ import annotations

import sys
from pathlib import Path


def _ask_mcp_block() -> str:
    if input("Add an MCP server now? [y/N] ").strip().lower() != "y":
        return ""
    name = input("  server name: ").strip()
    command = input("  command, space-separated (e.g. npx -y @modelcontextprotocol/server-github): ").strip()
    if not (name and command):
        return ""
    args = ", ".join(f'"{part}"' for part in command.split())
    return f"\nmcp:\n  - name: {name}\n    command: [{args}]\n"


def _report_credentials(path: Path) -> None:
    try:
        from .config import from_yaml
        from .credentials import missing_env_vars
    except ImportError:
        print("PyYAML not installed -- pip install pyacri[yaml] to run the credential check.", file=sys.stderr)
        return
    missing = missing_env_vars(from_yaml(path))
    if missing:
        print("set these before `acri up`/`acri studio`:")
        for var in missing:
            print(f"  {var}")
    else:
        print("credentials look good -- run `acri up` or `acri studio` next.")


def interactive_setup(path: Path) -> int:
    if path.exists():
        print(f"{path} already exists -- run `acri check {path}` to verify it, or edit it directly.")
        return 0
    if not sys.stdin.isatty():
        print("acri setup needs an interactive terminal -- run `acri init` for a non-interactive template.", file=sys.stderr)
        return 1

    provider = input("Model provider? [gemini/openai] (gemini): ").strip().lower() or "gemini"
    default_model = "gpt-4o-mini" if provider == "openai" else "gemini-2.5-flash"
    mcp_block = _ask_mcp_block()

    path.write_text(
        f"version: 1\n\nmodels:\n  default: {default_model}\n{mcp_block}\n"
        "resolve:\n  k: 5\n\nlimits:\n  timeout_ms: 5000\n  max_cost_per_task_usd: 0.05\n",
        encoding="utf-8",
    )
    note = "" if mcp_block else " (no mcp: servers -- add one by editing the file, or rerun setup)"
    print(f"wrote {path}{note}")
    _report_credentials(path)
    return 0
