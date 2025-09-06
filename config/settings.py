from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv


# Resolve repo root (one level up from this file's directory)
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"


@lru_cache(maxsize=1)
def load_env() -> bool:
    """Load environment variables from the project root `.env` file.

    Returns:
        bool: True if a .env file was found and loaded, False otherwise.
    """
    return load_dotenv(dotenv_path=ENV_PATH)


def get_reddit_config() -> Dict[str, str]:
    """Return Reddit API credentials from environment.

    Includes optional values if present to support password grant.

    Raises:
        RuntimeError: If required environment variables are missing.
    """
    load_env()
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "content-pipeline-script")

    if not client_id:
        raise RuntimeError(
            "Missing Reddit credentials. Please set REDDIT_CLIENT_ID in your environment or .env file."
        )

    creds: Dict[str, str] = {
        "client_id": client_id,
        "user_agent": user_agent,
    }

    # Optional values
    if client_secret:
        creds["client_secret"] = client_secret
    username = os.getenv("REDDIT_USERNAME")
    password = os.getenv("REDDIT_PASSWORD")
    if username and password:
        creds["username"] = username
        creds["password"] = password
    if os.getenv("REDDIT_INSTALLED_APP"):
        # Mark installed app to influence flow decisions in reddit_ingest
        creds["installed_app"] = os.getenv("REDDIT_INSTALLED_APP", "").lower()

    return creds


def get_openrouter_api_key() -> Optional[str]:
    """Return the OpenRouter API key, or None if not set."""
    load_env()
    return os.getenv("OPENROUTER_API_KEY")
