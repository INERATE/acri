"""mcp_connect — connect to acri.yaml's mcp: entries once at startup, return their tools.

Needs `mcp` (pip install pyacri[server]). Startup-only: `acri up` fetches
tools/list, then closes every connection -- it never calls tools/call itself
(the client executes tools, same as any OpenAI-compatible API), so nothing
needs to stay open while serving requests.
"""
from __future__ import annotations

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

from .adapters import from_mcp_tools
from .config import McpEntry
from .corpus import Tool
from .sandbox import sandboxed


def _stdio_params(entry: McpEntry) -> StdioServerParameters:
    if entry.sandbox:
        s = entry.sandbox
        return sandboxed(entry.command, s.image, memory=s.memory, cpus=s.cpus, network=s.network, volumes=s.volumes)
    return StdioServerParameters(command=entry.command[0], args=entry.command[1:])


async def _list_tools(entry: McpEntry) -> list[Tool]:
    transport = (
        stdio_client(_stdio_params(entry))
        if entry.command
        else streamable_http_client(entry.url)
    )
    async with transport as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        listed = await session.list_tools()
        raw = [{"name": t.name, "description": t.description or "", "inputSchema": t.input_schema} for t in listed.tools]
        return from_mcp_tools(raw)


async def connect_all(entries: list[McpEntry]) -> list[Tool]:
    """Connect to every entry in order, return the combined tool list."""
    tools: list[Tool] = []
    for entry in entries:
        tools.extend(await _list_tools(entry))
    return tools
