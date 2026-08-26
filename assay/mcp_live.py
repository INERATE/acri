"""mcp_live -- ingest tools from a REAL MCP server over stdio, resolve, execute, verify.

Not part of pytest/CI: spawns an external Node process and needs network on
first run to fetch the package. Proves acri.adapters.from_mcp_tools() against
the actual MCP wire protocol (initialize / tools/list / tools/call), not
Claude Code's own tool layer -- a genuinely independent integration test.

Run: python -m assay.mcp_live <allowed-directory> "<query>"
Needs Node.js (npx on PATH). No API key.
"""
from __future__ import annotations

import asyncio
import shutil
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from acri.adapters import from_mcp_tools
from acri.compass import resolve
from acri.corpus import index


async def run(allowed_dir: str, query: str) -> None:
    npx = shutil.which("npx")
    if npx is None:
        raise RuntimeError("npx not found on PATH -- Node.js is required for this test")

    params = StdioServerParameters(command=npx, args=["-y", "@modelcontextprotocol/server-filesystem", allowed_dir])

    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()

        listed = await session.list_tools()
        raw = [{"name": t.name, "description": t.description or "", "inputSchema": t.input_schema} for t in listed.tools]
        print(f"1. ingested {len(raw)} tools from a live MCP server (stdio, real JSON-RPC):")
        print("   " + ", ".join(t["name"] for t in raw))

        corpus = index(from_mcp_tools(raw))
        resolved = resolve(query, corpus, k=3)
        print(f"\n2. resolve({query!r}, k=3):")
        for r in resolved:
            print(f"   {r.tool.name:<22} score={r.score:.3f}")
        if not resolved:
            raise RuntimeError("resolve() returned nothing -- cannot proceed to a live call")

        top = resolved[0].tool
        args = {"path": allowed_dir} if "path" in top.parameters.get("properties", {}) else {}
        print(f"\n3. calling the top-ranked tool live: {top.name}({args})")
        result = await session.call_tool(top.name, args)
        text = "".join(getattr(c, "text", "") for c in result.content)
        print("   live result:", text.strip().replace("\n", " | "))

        assert "marker.txt" in text, f"expected the known marker file in the live result, got: {text!r}"
        print("\nverified: marker.txt (planted before this run) is in the live tool result.")
        print("ingest -> resolve -> execute is a real pipeline against a real MCP server, not a mock.")


if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    query = sys.argv[2] if len(sys.argv) > 2 else "what files are in this directory"
    asyncio.run(run(directory, query))
