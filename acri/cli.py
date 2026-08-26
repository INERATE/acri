"""cli — argv parsing and dispatch only. Handlers live in _commands.py."""
from __future__ import annotations

import sys
from argparse import ArgumentParser

from . import _commands as cmd


def main(argv: list[str] | None = None) -> int:
    parser = ArgumentParser(prog="acri", description="A client-side capability resolver -- pick the right few tools before the request is sent.")
    sub = parser.add_subparsers(dest="command")

    p_setup = sub.add_parser("setup", help="guided acri.yaml setup: provider, one mcp server, a credential check")
    p_setup.add_argument("path", nargs="?", default="acri.yaml")
    p_setup.set_defaults(func=cmd.setup)

    p_init = sub.add_parser("init", help="write a template acri.yaml")
    p_init.add_argument("path", nargs="?", default="acri.yaml")
    p_init.set_defaults(func=cmd.init)

    p_check = sub.add_parser("check", help="validate acri.yaml and its credentials")
    p_check.add_argument("path", nargs="?", default="acri.yaml")
    p_check.set_defaults(func=cmd.check)

    p_up = sub.add_parser("up", help="run the daemon: an OpenAI-compatible endpoint over acri.yaml's tools")
    p_up.add_argument("path", nargs="?", default="acri.yaml")
    p_up.add_argument("--host", default="127.0.0.1")
    p_up.add_argument("--port", type=int, default=8080)
    p_up.add_argument("--log-conversations", action="store_true")
    p_up.set_defaults(func=cmd.up)

    p_studio = sub.add_parser("studio", help="run the read-only dashboard over acri.yaml and the ledger")
    p_studio.add_argument("path", nargs="?", default="acri.yaml")
    p_studio.add_argument("--ledger", default=".acri/ledger.jsonl")
    p_studio.add_argument("--host", default="127.0.0.1")
    p_studio.add_argument("--port", type=int, default=8099)
    p_studio.set_defaults(func=cmd.studio)

    args = parser.parse_args(argv)
    if args.command is None:  # bare `acri` -- help, not an error, since nothing went wrong
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
