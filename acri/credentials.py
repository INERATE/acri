"""credentials — which env vars a Config's models need, and which are missing.

Split out of config.py: parsing acri.yaml and checking credentials are
different concerns that happen to both feed `acri check`.
"""
from __future__ import annotations

import os

from .config import Config

_ENV_VARS = {"gemini": "GEMINI_API_KEY", "openai": "OPENAI_API_KEY"}


def provider_for(model: str) -> str:
    return "gemini" if "gemini" in model.lower() else "openai"


def missing_env_vars(config: Config) -> list[str]:
    """Standard env vars (GEMINI_API_KEY, OPENAI_API_KEY) any configured model needs,
    that aren't set. Inferred from the model name, not a `provider:` field -- the
    documented acri.yaml example doesn't have one."""
    models = [m for m in (config.models.default, config.models.cheap) if m]
    needed = {_ENV_VARS[provider_for(m)] for m in models}
    return sorted(v for v in needed if not os.environ.get(v))
