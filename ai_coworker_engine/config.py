"""
Configuration utilities.

We keep this file intentionally small:
- Loads environment variables (optionally from a local .env)
- Exposes the OpenAI API key and model name
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """App settings loaded from environment variables."""

    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash"


def load_settings() -> Settings:
    """
    Load settings from environment variables.

    Uses python-dotenv so local development can use a `.env` file,
    while production environments can inject env vars directly.
    """

    load_dotenv(override=False)
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()

    if not api_key:
        raise RuntimeError(
            "Missing GEMINI_API_KEY. Set it in your environment (or a local .env)."
        )

    return Settings(gemini_api_key=api_key, gemini_model=model)


