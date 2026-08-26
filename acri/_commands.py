"""_commands — the five `acri` subcommand handlers. Split out of cli.py
(word-cap): argv parsing/dispatch is a different concern from what each
subcommand actually does.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ._setup import ensure_config, run_safely
from ._template import TEMPLATE
from ._wizard import interactive_setup


def init(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if path.exists():
        print(f"{path} already exists -- not overwriting.", file=sys.stderr)
        return 1
    path.write_text(TEMPLATE, encoding="utf-8")
    print(f"wrote {path}")
    return 0


def setup(args: argparse.Namespace) -> int:
    return interactive_setup(Path(args.path))


def check(args: argparse.Namespace) -> int:
    try:
        from .config import from_yaml  # lazy
        from .credentials import missing_env_vars
    except ImportError:
        print("acri check needs PyYAML -- pip install pyacri[yaml]", file=sys.stderr)
        return 1
    path = Path(args.path)
    if (code := ensure_config(path)) is not None:
        return code
    missing = missing_env_vars(from_yaml(path))
    if missing:
        print("missing credentials:")
        for var in missing:
            print(f"  {var}")
        return 1
    print(f"ok - {path} is valid, all credentials present")
    return 0


def up(args: argparse.Namespace) -> int:
    try:
        from .server import serve  # lazy
    except ImportError:
        print("acri up needs mcp and PyYAML -- pip install pyacri[server]", file=sys.stderr)
        return 1
    if (code := ensure_config(Path(args.path))) is not None:
        return code
    return run_safely("acri up", serve, args.path, host=args.host, port=args.port, log_conversations=args.log_conversations)


def studio(args: argparse.Namespace) -> int:
    try:
        from .studio import serve_studio  # lazy
    except ImportError:
        print("acri studio needs PyYAML -- pip install pyacri[studio]", file=sys.stderr)
        return 1
    if (code := ensure_config(Path(args.path))) is not None:
        return code
    return run_safely("acri studio", serve_studio, args.path, ledger_path=args.ledger, host=args.host, port=args.port)
