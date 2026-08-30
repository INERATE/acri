"""_client_factory — builds a live SDK client for `acri up`, one per provider.

Split out of server.py (file-size cap, and construction is its own concern).
Every SDK import stays lazy: `acri up` only needs whichever one provider is
actually configured installed, not all twelve.
"""
from __future__ import annotations

import os
from typing import Any

# provider -> (base_url, api-key env var). Every entry here speaks OpenAI's
# wire format -- openai_compatible() handles all of them unchanged; only the
# endpoint and which key differ. Local servers ignore the key value itself,
# but the SDK requires a non-empty string.
_OPENAI_COMPAT: dict[str, tuple[str, str | None]] = {
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "nvidia": ("https://integrate.api.nvidia.com/v1", "NVIDIA_API_KEY"),
    "grok": ("https://api.x.ai/v1", "XAI_API_KEY"),
    "ollama": (os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"), None),
    "vllm": (os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1"), None),
    "lmstudio": (os.environ.get("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"), None),
}


def client_for(provider: str) -> Any:
    if provider == "gemini":
        from google import genai

        return genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    if provider == "vertex":
        from google import genai

        return genai.Client(vertexai=True, project=os.environ["GOOGLE_CLOUD_PROJECT"],
                             location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"))
    if provider == "anthropic":
        import anthropic

        return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    if provider == "vertex-claude":
        from anthropic import AnthropicVertex

        return AnthropicVertex(project_id=os.environ["GOOGLE_CLOUD_PROJECT"],
                                region=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"))
    if provider == "bedrock":
        import boto3

        return boto3.client("bedrock-runtime")  # boto3's own credential chain -- acri touches none of it
    if provider == "openai":
        import openai

        return openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    if provider == "cloudflare":
        import openai

        account_id = os.environ["CLOUDFLARE_ACCOUNT_ID"]
        return openai.OpenAI(base_url=f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1",
                              api_key=os.environ["CLOUDFLARE_API_TOKEN"])
    if provider == "azure-grok":
        import openai

        return openai.OpenAI(base_url=os.environ["AZURE_AI_ENDPOINT"], api_key=os.environ["AZURE_AI_API_KEY"])
    if provider in _OPENAI_COMPAT:
        import openai

        base_url, key_env = _OPENAI_COMPAT[provider]
        return openai.OpenAI(base_url=base_url, api_key=os.environ.get(key_env, "not-needed") if key_env else "not-needed")
    raise ValueError(f"unknown provider: {provider!r}")
