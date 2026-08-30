"""providers — the one canonical "provider name -> which wire format" table.

Before this file, three places each kept their own copy (acri/__init__.py's
run(), assay/accuracy.py, and implicitly server.py) -- the exact "hardcoded,
can drift" complaint that prompted this file. Client CONSTRUCTION (API keys,
base_urls, which SDK to import) is deliberately NOT here: acri's core stays
dependency-free (port.py's docstring), so that lives in server.py._client_for
(production) and assay/clients.py (the benchmark script), both outside it.

Providers that speak OpenAI's wire format (cloudflare, openrouter, nvidia,
grok, and any local server -- ollama, vllm, lmstudio) all reuse
openai_compatible() unchanged; only their client's base_url differs.
"""
from __future__ import annotations

from typing import Any, Callable

from .port import openai_compatible
from .port_anthropic import anthropic
from .port_bedrock import bedrock
from .port_gemini import gemini

PROVIDERS: dict[str, Callable[..., Any]] = {
    "openai": openai_compatible,
    "gemini": gemini,
    "vertex": gemini,  # same wire format as gemini, auth-only difference (clients.py)
    "anthropic": anthropic,
    "vertex-claude": anthropic,  # Claude-on-Vertex speaks Anthropic's wire format, not Gemini's --
    # AnthropicVertex (clients.py) is a drop-in client, same .messages.create() shape.
    "bedrock": bedrock,
    "cloudflare": openai_compatible,
    "azure-grok": openai_compatible,  # xAI Grok on Azure AI Foundry's newer /openai/v1 surface --
    # OpenAI-SDK-compatible auth, same chat-completions shape, only base_url/key differ.
    "openrouter": openai_compatible,
    "nvidia": openai_compatible,
    "grok": openai_compatible,
    "ollama": openai_compatible,
    "vllm": openai_compatible,
    "lmstudio": openai_compatible,
}
