"""cli — `acri init` writes a template acri.yaml; `acri check` validates one;
`acri up` runs the daemon; `acri studio` runs the read-only dashboard. Both
ship ahead of decisions.md's own gates, at the maintainer's request -- see
acri/server.py and acri/studio.py for specifics.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ._template import TEMPLATE


def _init(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if path.exists():
        print(f"{path} already exists -- not overwriting.", file=sys.stderr)
        return 1
    path.write_text(TEMPLATE, encoding="utf-8")
    print(f"wrote {path}")
    return 0


def _check(args: argparse.Namespace) -> int:
    try:
        from .config import from_yaml  # lazy: needs pyacri[yaml]
        from .credentials import missing_env_vars
    except ImportError:
        print("acri check needs PyYAML -- pip install pyacri[yaml]", file=sys.stderr)
        return 1
    path = Path(args.path)
    if not path.exists():
        print(f"{path} not found -- run `acri init` first.", file=sys.stderr)
        return 1
    missing = missing_env_vars(from_yaml(path))
    if missing:
        print("missing credentials:")
        for var in missing:
            print(f"  {var}")
        return 1
    print(f"ok - {path} is valid, all credentials present")
    return 0


def _up(args: argparse.Namespace) -> int:
    try:
        from .server import serve  # lazy: needs pyacri[server]
    except ImportError:
        print("acri up needs mcp and PyYAML -- pip install pyacri[server]", file=sys.stderr)
        return 1
    serve(args.path, host=args.host, port=args.port, log_conversations=args.log_conversations)
    return 0


def _studio(args: argparse.Namespace) -> int:
    try:
        from .studio import serve_studio  # lazy: needs pyacri[yaml]
    except ImportError:
        print("acri studio needs PyYAML -- pip install pyacri[studio]", file=sys.stderr)
        return 1
    serve_studio(args.path, ledger_path=args.ledger, host=args.host, port=args.port)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="acri")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="write a template acri.yaml")
    p_init.add_argument("path", nargs="?", default="acri.yaml")
    p_init.set_defaults(func=_init)

    p_check = sub.add_parser("check", help="validate acri.yaml and its credentials")
    p_check.add_argument("path", nargs="?", default="acri.yaml")
    p_check.set_defaults(func=_check)

    p_up = sub.add_parser("up", help="run the daemon: an OpenAI-compatible endpoint over acri.yaml's tools")
    p_up.add_argument("path", nargs="?", default="acri.yaml")
    p_up.add_argument("--host", default="127.0.0.1")
    p_up.add_argument("--port", type=int, default=8080)
    p_up.add_argument("--log-conversations", action="store_true")
    p_up.set_defaults(func=_up)

    p_studio = sub.add_parser("studio", help="run the read-only dashboard over acri.yaml and the ledger")
    p_studio.add_argument("path", nargs="?", default="acri.yaml")
    p_studio.add_argument("--ledger", default=".acri/ledger.jsonl")
    p_studio.add_argument("--host", default="127.0.0.1")
    p_studio.add_argument("--port", type=int, default=8099)
    p_studio.set_defaults(func=_studio)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
