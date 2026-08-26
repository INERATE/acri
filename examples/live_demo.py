"""live_demo — acri end to end: a real MCP server, live resolution, a cached call.

Run: python examples/live_demo.py [directory] ["query"]
Needs Node.js (npx on PATH) for the MCP part -- no API key required for that.
Set GEMINI_API_KEY to also see acri.run() hit a real model and then hit cache
on a repeat; without it, that part is skipped and explained, not faked with
a stub client.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import acri
from acri.adapters import from_mcp_tools


async def main(directory: str, query: str) -> None:
    npx = shutil.which("npx")
    if npx is None:
        raise SystemExit("npx not found on PATH -- Node.js is required for this demo")

    params = StdioServerParameters(command=npx, args=["-y", "@modelcontextprotocol/server-filesystem", directory])
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        listed = await session.list_tools()
        raw = [{"name": t.name, "description": t.description or "", "inputSchema": t.input_schema} for t in listed.tools]
        corpus = acri.index(from_mcp_tools(raw))
        print(f"connected to a real MCP server: {len(corpus)} tools")

        resolved = acri.resolve(query, corpus, k=3)
        print(f"resolve({query!r}) -> {[r.tool.name for r in resolved]}")

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("\nGEMINI_API_KEY not set -- skipping the live call + cache part.")
            print("set it and rerun to see acri.run() call a real model, then hit cache on a repeat.")
            return

        from google import genai

        client = genai.Client(api_key=api_key)
        cache: dict = {}
        for label in ("first call", "repeat (same query -- should hit cache)"):
            start = time.perf_counter()
            result = acri.run(query, corpus, client, provider="gemini", k=3, cache=cache)
            elapsed = (time.perf_counter() - start) * 1000
            print(f"{label}: {elapsed:.1f}ms, tool_calls={result.tool_calls}")


if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    query = sys.argv[2] if len(sys.argv) > 2 else "what files are in this directory"
    asyncio.run(main(directory, query))
