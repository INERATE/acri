"""credentials — which env var a model's provider needs, and which are missing.

Split out of config.py: parsing acri.yaml and checking credentials are
different concerns that happen to both feed `acri check`.
"""
from __future__ import annotations

import os

from .config import Config
from .providers import PROVIDERS

# One canonical entry per acri.providers.PROVIDERS key -- `acri check` names
# the single env var most commonly missing, not every variant an SDK's full
# credential chain accepts (Bedrock/Vertex both take several). A local server
# (Ollama/vLLM/LM Studio) needs no key at all: None.
_ENV_VARS: dict[str, str | None] = {
    "gemini": "GEMINI_API_KEY", "vertex": "GOOGLE_APPLICATION_CREDENTIALS",
    "vertex-claude": "GOOGLE_APPLICATION_CREDENTIALS",
    "openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY",
    "bedrock": "AWS_ACCESS_KEY_ID", "cloudflare": "CLOUDFLARE_API_TOKEN",
    "openrouter": "OPENROUTER_API_KEY", "nvidia": "NVIDIA_API_KEY", "grok": "XAI_API_KEY",
    "ollama": None, "vllm": None, "lmstudio": None,
}
assert set(_ENV_VARS) == set(PROVIDERS), "every acri.providers.PROVIDERS entry needs an _ENV_VARS row"


def provider_for(model: str) -> str:
    """"provider/model" (e.g. "openrouter/meta-llama/llama-3.3-70b") names its
    provider explicitly and wins. A bare model name (no "/") falls back to the
    two providers acri has always inferred this way -- the acri.yaml already
    shipped in v0.5.0 never had a "/" in a model name, so this stays exact."""
    if "/" in model:
        provider, _, _ = model.partition("/")
        return provider
    return "gemini" if "gemini" in model.lower() else "openai"


def model_id_for(model: str) -> str:
    """Strip acri's own "provider/" prefix, if any -- the literal id an SDK call
    needs. Splits on the first "/" only: OpenRouter/NVIDIA model ids are
    themselves "vendor/model" and must survive that intact after the strip."""
    _, sep, rest = model.partition("/")
    return rest if sep else model


def missing_env_vars(config: Config) -> list[str]:
    """Env vars any configured model's provider needs, that aren't set.
    Raises ValueError on a typo'd/unknown provider -- fail at config-load
    time, not with a silent "no key needed"."""
    models = [m for m in (config.models.default, config.models.cheap) if m]
    for m in models:
        p = provider_for(m)
        if p not in _ENV_VARS:
            raise ValueError(f"unknown provider {p!r} in model {m!r} (expected one of {sorted(_ENV_VARS)})")
    needed = {_ENV_VARS[provider_for(m)] for m in models}
    return sorted(v for v in needed if v and not os.environ.get(v))
