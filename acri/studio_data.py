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

CORPUS_SNAPSHOT_PATH = Path(".acri/corpus.json")


def read_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_corpus_snapshot(corpus: Any, path: Path = CORPUS_SNAPSHOT_PATH) -> None:
    """Called once by `acri up` right after it builds the real corpus (it's
    the one process that legitimately connects to every MCP server). Lets
    studio show the *full* registered tool set -- including tools never
    resolved into a request yet -- without studio connecting to anything
    itself (decisions.md's read-only boundary)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    names = [t.name for t in corpus.tools]
    path.write_text(json.dumps(names), encoding="utf-8")


def _read_corpus_snapshot(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def topology(config: Any, ledger_path: Path, corpus_path: Path = CORPUS_SNAPSHOT_PATH) -> dict[str, Any]:
    """Servers and models straight from acri.yaml. Tool names come from two
    sources merged: ledger history (`seen` count -- how often each was
    actually offered) and, if `acri up` has run at least once, the full
    corpus snapshot (tools never offered yet appear with `seen: 0`, the
    dashboard's "hidden layer"). No live MCP connection either way.
    `server` is a name-prefix guess (`github_get_pr` -> `github`), a hint,
    not a guarantee."""
    seen = Counter(name for e in read_ledger(ledger_path) for name in e.get("offered", []))
    names = set(seen) | set(_read_corpus_snapshot(corpus_path))
    tools = [{"name": n, "server": (_TOOL_PREFIX.match(n) or [None, None])[1], "seen": seen.get(n, 0)} for n in names]
    servers = [{"name": m.name, "target": m.command[0] if m.command else m.url, "sandboxed": m.sandbox is not None} for m in config.mcp]
    return {"servers": servers, "models": asdict(config.models), "tools": tools}


def recent(ledger_path: Path, limit: int = 200) -> list[dict[str, Any]]:
    """Newest first, capped at `limit` -- a live dashboard shows what just
    happened, not the whole history; the file itself is unaffected."""
    return read_ledger(ledger_path)[-limit:][::-1]
