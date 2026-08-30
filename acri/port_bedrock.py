"""port_bedrock — the AWS Bedrock native adapter. See port_gemini.py's docstring
for why each native provider gets its own file.
"""
from __future__ import annotations

from typing import Any

from .compass import Resolved
from .port import GenerationResult
from .schemas import to_bedrock_tools


def bedrock(client: Any, prompt: str, resolved: list[Resolved], model: str = "us.anthropic.claude-sonnet-4-6") -> GenerationResult:
    """Call a Bedrock Converse API client (boto3 `bedrock-runtime` client's `.converse()`)."""
    tools = to_bedrock_tools(resolved)
    kwargs: dict[str, Any] = {"modelId": model, "messages": [{"role": "user", "content": [{"text": prompt}]}]}
    if tools:
        kwargs["toolConfig"] = {"tools": tools}
    response = client.converse(**kwargs)
    # Same defensive shape as gemini() -- a guardrail intervention or a
    # max-tokens stop before any content can leave "message" absent entirely.
    blocks = response.get("output", {}).get("message", {}).get("content") or []
    text = None
    calls = []
    for block in blocks:
        if "text" in block:
            text = block["text"]
        if "toolUse" in block:
            use = block["toolUse"]
            calls.append({"name": use["name"], "arguments": use.get("input", {})})
    return GenerationResult(text=text, tool_calls=calls, raw=response)
