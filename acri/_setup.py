"""_setup — shared "is acri.yaml actually usable" checks for cli.py.

Split out of cli.py (word-cap): this is onboarding/error-message logic, not
argv parsing. `check`/`up`/`studio` all need the same "acri.yaml is missing"
handling -- fixed once here so a future subcommand gets it for free too,
instead of a fourth copy of the same check.
"""
from __future__ import annotations

import sys
from pathlib import Path

from ._template import TEMPLATE


def ensure_config(path: Path) -> int | None:
    """None if `path` exists (caller proceeds). Otherwise, at a real terminal,
    offers to run `acri init` right there -- never prompts a non-interactive
    caller (a daemon supervisor, a script), which would just hang forever
    waiting for input that never comes. A freshly-templated acri.yaml still
    needs real mcp:/models: values before anything can actually run, so this
    never chains into retrying the original command -- it names the next
    step and returns the exit code to return immediately."""
    if path.exists():
        return None
    if sys.stdin.isatty() and input(f"{path} not found. Run `acri init` now? [y/N] ").strip().lower() == "y":
        path.write_text(TEMPLATE, encoding="utf-8")
        print(f"wrote {path} -- add your mcp: servers and model, then rerun.")
    else:
        print(f"{path} not found -- run `acri init` first.", file=sys.stderr)
    return 1


def run_safely(label: str, call: object, *args: object, **kwargs: object) -> int:
    """Call `call(*args, **kwargs)`; on a misconfiguration (bad yaml, no mcp:
    servers, missing credentials -- anything raised before a server actually
    starts serving), print one clean line instead of a raw traceback. Doesn't
    swallow KeyboardInterrupt (Ctrl+C to stop a running daemon) -- that's not
    an Exception subclass in Python, so it isn't caught here."""
    try:
        call(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 -- deliberately broad, see docstring
        print(f"{label}: {exc}", file=sys.stderr)
        return 1
    return 0
