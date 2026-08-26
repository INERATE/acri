"""corpus — the capability index. Ingests tools into one searchable body, once."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


@dataclass(frozen=True)
class Tool:
    """One capability: a name, a description, a JSON Schema, and how to reach it.

    `handler` is optional — resolution never calls it. It's a place for the
    caller (or a future dispatcher) to find the actual function.
    """

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=lambda: {"type": "object", "properties": {}})
    handler: Callable[..., Any] | None = None


@dataclass
class Corpus:
    """A built capability index. Construct with `index()`, not directly.

    The four fields below are the prebuilt BM25 index that `compass.resolve`
    reads — treat this as an opaque handle unless you're changing the ranking.
    """

    tools: list[Tool]
    doc_tokens: list[list[str]]
    doc_freqs: list[dict[str, int]]
    df: dict[str, int]
    avgdl: float

    def __len__(self) -> int:
        return len(self.tools)


def index(tools: list[Tool]) -> Corpus:
    """Build a searchable Corpus once. Reuse it across turns — never rebuild per query."""
    if not tools:
        raise ValueError("index() needs at least one tool")
    doc_tokens = [_tokenize(f"{t.name} {t.description}") for t in tools]
    doc_freqs: list[dict[str, int]] = []
    df: dict[str, int] = {}
    for tokens in doc_tokens:
        freqs: dict[str, int] = {}
        for tok in tokens:
            freqs[tok] = freqs.get(tok, 0) + 1
        doc_freqs.append(freqs)
        for tok in freqs:
            df[tok] = df.get(tok, 0) + 1
    avgdl = sum(len(t) for t in doc_tokens) / len(doc_tokens)
    return Corpus(tools=list(tools), doc_tokens=doc_tokens, doc_freqs=doc_freqs, df=df, avgdl=avgdl)
