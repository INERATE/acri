"""ledger — the decision trace. What was offered, what was chosen, what it cost.

v0.1 is deliberately just this: an in-memory list plus an optional JSONL
append. `studio` (a live visualizer over OpenTelemetry spans) and a real
cost model are later work — see docs/decisions.md. This module makes no
claim about cost; `cost_usd` is None unless the caller computes and passes it.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .compass import Resolved


@dataclass(frozen=True)
class Entry:
    """One resolved task: what was offered, what the model picked, what it cost."""

    query: str
    offered: list[str]
    selected: list[str]
    latency_ms: float
    cost_usd: float | None = None
    timestamp: float = field(default_factory=time.time)


class Ledger:
    """Collects Entries in memory and, if given a path, appends each one as JSONL."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.entries: list[Entry] = []
        self._path = Path(path) if path else None

    def record(
        self,
        query: str,
        offered: list[Resolved],
        selected: list[str],
        latency_ms: float,
        cost_usd: float | None = None,
    ) -> Entry:
        entry = Entry(
            query=query,
            offered=[r.tool.name for r in offered],
            selected=selected,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
        )
        self.entries.append(entry)
        if self._path:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(entry)) + "\n")
        return entry
