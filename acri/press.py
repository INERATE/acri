"""press — the compactor. docs/architecture.md #3, decisions.md "where TOON goes".

Large tool RESULTS (never schemas -- those reach port unchanged) become a
short digest plus a handle to the full result. architecture.md #8 names
the open risk as a digest dropping the one identifier a later turn needed;
the handle is the answer -- nothing is discarded, only deferred, and
`recover()` gets it back.

TOON-style tabular encoding for uniform lists-of-dicts (header row once,
not per row) -- decisions.md: that's where TOON genuinely wins, versus
nested schemas, its documented worst case. Not the toon-format PyPI
package: its encode() raises NotImplementedError as of 0.1.0, checked
directly before writing this instead of depending on it.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Pressed:
    digest: str
    handle: str | None  # None means nothing was dropped -- digest is the whole result
    full_chars: int


def _is_uniform_table(value: Any) -> bool:
    return (isinstance(value, list) and bool(value) and all(isinstance(r, dict) for r in value)
            and len({tuple(sorted(r.keys())) for r in value}) == 1)


def _toon_table(rows: list[dict]) -> str:
    keys = list(rows[0].keys())
    lines = [",".join(keys)] + [",".join(str(row.get(k, "")) for k in keys) for row in rows]
    return "\n".join(lines)


def press(result: Any, store: dict[str, Any], *, max_rows: int = 20, max_chars: int = 2000) -> Pressed:
    """Compact `result` if it's over `max_chars`, storing the untruncated
    version in `store` (caller-owned, same pattern as acri.run()'s cache)
    under a fresh handle."""
    full_json = json.dumps(result, separators=(",", ":"), default=str)
    if len(full_json) <= max_chars:
        return Pressed(digest=full_json, handle=None, full_chars=len(full_json))

    handle = f"press:{len(store)}"
    store[handle] = result

    if _is_uniform_table(result):
        shown = result[:max_rows]
        digest = _toon_table(shown)
        if len(result) > max_rows:
            digest += f"\n... {len(result) - max_rows} more rows, full result at handle {handle!r}"
    else:
        digest = full_json[:max_chars] + f"... truncated, full result at handle {handle!r}"

    return Pressed(digest=digest, handle=handle, full_chars=len(full_json))


def recover(handle: str, store: dict[str, Any]) -> Any:
    """The fidelity answer: get back exactly what press() truncated away."""
    return store[handle]
