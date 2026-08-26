"""sandbox — resource and network limits on stdio MCP servers, v1.1.

docs/decisions.md: MCP already separates processes (a stdio server is
already a subprocess, not code in your interpreter) -- the genuine gap is
CPU/memory/network *limits*. Calls the host container engine; never
reimplements namespaces or cgroups, which is writing runc.

No sandboxing is the default for every mcp: entry -- this only applies
when a caller explicitly opts an entry in via acri.yaml's `sandbox:` key,
because it changes what the server can reach (least of all: filesystem
servers rooted outside the container won't see the host filesystem at
all unless volume-mounted, which this does not do).
"""
from __future__ import annotations

from mcp import StdioServerParameters


def sandboxed(
    command: list[str],
    image: str,
    *,
    memory: str = "256m",
    cpus: float = 0.5,
    network: bool = True,
) -> StdioServerParameters:
    """Wrap `command` to run inside `image` via `docker run -i --rm` instead of
    directly on the host. The result still speaks MCP over stdio -- whatever
    calls stdio_client() on it doesn't need to know docker is in between."""
    args = ["run", "-i", "--rm", f"--memory={memory}", f"--cpus={cpus}"]
    if not network:
        args.append("--network=none")
    args.append(image)
    args.extend(command)
    return StdioServerParameters(command="docker", args=args)
