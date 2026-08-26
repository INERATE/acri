"""studio_data — reads acri.yaml + .acri/ledger.jsonl for the studio dashboard.

Split out of studio.py on the word-cap hook: this is data shaping, studio.py
is HTTP serving. Read-only -- no MCP connection, no model call.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

_TOOL_PREFIX = re.compile(r"^([a-z0-9]+)_")


def read_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def topology(config: Any, ledger_path: Path) -> dict[str, Any]:
    """Servers and models straight from acri.yaml; tool names from ledger
    history (every tool ever offered was already recorded by name -- no live
    MCP connection needed to know they exist). `server` is a name-prefix
    guess (`github_get_pr` -> `github`), shown as a hint, not a guarantee."""
    seen = Counter(name for e in read_ledger(ledger_path) for name in e.get("offered", []))
    tools = [{"name": n, "server": (_TOOL_PREFIX.match(n) or [None, None])[1], "seen": c} for n, c in seen.items()]
    servers = [{"name": m.name, "target": m.command[0] if m.command else m.url, "sandboxed": m.sandbox is not None} for m in config.mcp]
    return {"servers": servers, "models": asdict(config.models), "tools": tools}


def recent(ledger_path: Path, limit: int = 200) -> list[dict[str, Any]]:
    """Newest first, capped at `limit` -- a live dashboard shows what just
    happened, not the whole history; the file itself is unaffected."""
    return read_ledger(ledger_path)[-limit:][::-1]
