"""Paths and constants for the xp CLI."""
import os
from pathlib import Path

APP_NAME = "xp"

# Base URL of the web service xp talks to.
# Override with the XP_BASE_URL env var for local dev, e.g.:

DEV_BASE_URL = "http://127.0.0.1:8081"
DEFAULT_BASE_URL = "https://olimn.com"


def get_base_url() -> str:
    return os.environ.get("XP_BASE_URL", DEV_BASE_URL)


def get_config_dir() -> Path:
    d = Path.home() / f".{APP_NAME}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_credentials_path() -> Path:
    return get_config_dir() / "credentials.json"
