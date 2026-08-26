"""fixtures — load the labeled benchmark corpus. Data lives in fixtures.json, not here.

100 tools across 20 domains (github, postgres, slack, stripe, aws_ec2, ...),
including same-shape pairs across domains (jira vs zendesk tickets) so a
resolver can't win on name alone. 52 hand-written queries, phrased the way a
person actually types them — not paraphrases of the tool descriptions, which
would trivially inflate lexical recall. 2 are adversarial: no correct answer
exists in the corpus (`tool: null`), to check the resolver doesn't force one.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from acri.adapters import from_mcp_tools
from acri.corpus import Tool

_DEFAULT = Path(__file__).parent / "fixtures.json"


@dataclass(frozen=True)
class GoldQuery:
    query: str
    tool: str | None  # None means: no tool in the corpus should match


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_tools(path: Path = _DEFAULT) -> list[Tool]:
    # fixtures.json stores each tool as a real MCP tools/list entry
    # (inputSchema included) and goes through the same adapter a live MCP
    # server's response would -- see assay/mcp_live.py. `path` defaults to
    # the 100-tool corpus; assay/scale.py points it at fixtures_500.json.
    return from_mcp_tools(_load(path)["tools"])


def load_gold(path: Path = _DEFAULT) -> list[GoldQuery]:
    return [GoldQuery(query=g["query"], tool=g["tool"]) for g in _load(path)["gold"]]
