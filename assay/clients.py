"""clients — construct a live provider client from an env var. Only accuracy.py needs this."""
from __future__ import annotations

import os


def openai_client():
    import openai

    return openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def gemini_client():
    from google import genai

    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def vertex_client():
    # Same models, a different door: ADC instead of an API key. Needs
    # GOOGLE_APPLICATION_CREDENTIALS pointing at a service-account key and
    # GOOGLE_CLOUD_PROJECT set — google-auth reads both, acri touches neither.
    from google import genai

    return genai.Client(
        vertexai=True,
        project=os.environ["GOOGLE_CLOUD_PROJECT"],
        location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
    )


CLIENTS = {"openai": openai_client, "gemini": gemini_client, "vertex": vertex_client}
