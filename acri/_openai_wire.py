"""_openai_wire — parsing helpers for OpenAI-shaped request content.

Split out of daemon.py (file-size cap): wire-format parsing is a different
concern from _text.py's BM25 tokenization, even though both end up feeding
compass.resolve() a plain string.
"""
from __future__ import annotations

from typing import Any


def extract_text(content: Any) -> str:
    """The text portion of an OpenAI-shaped message `content` -- itself, if already a
    plain string, or the joined `text` parts of a multimodal list. compass.resolve()
    needs real text tokens regardless of what else (an image, audio) rides along."""
    if isinstance(content, str):
        return content
    return " ".join(part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text")
