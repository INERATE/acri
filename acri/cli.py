"""cli — `acri init` writes a template acri.yaml; `acri check` validates one;
`acri up` runs the daemon (acri/server.py) -- built ahead of decisions.md's own
gate ("after the library has users who want it") at the maintainer's explicit
request; see that commit message, not this one, for the override itself.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

TEMPLATE = """\
version: 1

models:
  default: gemini-2.5-flash
  # cheap: a stateless, prefix-free tier only -- classification, extraction,
  # summarizing a tool result. See docs/architecture.md #4.4. Optional.
  # cheap: gemini-2.5-flash-lite

mcp:
  # - name: github
  #   command: ["npx", "-y", "@modelcontextprotocol/server-github"]
  # - name: postgres
  #   url: http://localhost:3001

resolve:
  k: 5

limits:
  timeout_ms: 5000
  max_cost_per_task_usd: 0.05
"""


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
        from .config import from_yaml  # lazy: needs acri[yaml]
        from .credentials import missing_env_vars
    except ImportError:
        print("acri check needs PyYAML -- pip install acri[yaml]", file=sys.stderr)
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
        from .server import serve  # lazy: needs acri[server]
    except ImportError:
        print("acri up needs mcp and PyYAML -- pip install acri[server]", file=sys.stderr)
        return 1
    serve(args.path, host=args.host, port=args.port, log_conversations=args.log_conversations)
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

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
