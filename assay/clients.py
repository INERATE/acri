"""clients — construct a live provider client from an env var. Only accuracy.py needs this."""
from __future__ import annotations

import os


def openai_client():
    import openai

    return openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def gemini_client():
    from google import genai

    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


CLIENTS = {"openai": openai_client, "gemini": gemini_client}
