"""sandbox — resource, network, and filesystem limits on stdio MCP servers, v1.1.

docs/decisions.md: MCP already separates processes (a stdio server is
already a subprocess, not code in your interpreter) -- the genuine gap is
CPU/memory/network *limits*. Calls the host container engine; never
reimplements namespaces or cgroups, which is writing runc.

No sandboxing is the default for every mcp: entry -- this only applies
when a caller explicitly opts an entry in via acri.yaml's `sandbox:` key,
because it changes what the server can reach: filesystem servers rooted
outside the container won't see the host filesystem at all unless a path
is named in `volumes`.
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
    volumes: dict[str, str] | None = None,
) -> StdioServerParameters:
    """Wrap `command` to run inside `image` via `docker run -i --rm` instead of
    directly on the host. The result still speaks MCP over stdio -- whatever
    calls stdio_client() on it doesn't need to know docker is in between.

    `volumes` maps host path -> container path (`-v host:container`), so a
    sandboxed filesystem/git server can reach a real project folder. Append
    `:ro` to a container path yourself for a read-only mount -- one string,
    no separate flag."""
    args = ["run", "-i", "--rm", f"--memory={memory}", f"--cpus={cpus}"]
    if not network:
        args.append("--network=none")
    for host, container in (volumes or {}).items():
        args.extend(["-v", f"{host}:{container}"])
    args.append(image)
    args.extend(command)
    return StdioServerParameters(command="docker", args=args)
