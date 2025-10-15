from __future__ import annotations

from pathlib import Path

import dotenv
from platformdirs import user_cache_dir, user_config_dir


def get_dotenv_path() -> Path:
    """Return the path to the .env file in the user config directory."""
    config_dir = Path(user_config_dir("kabukit"))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / ".env"


def set_key(key: str, value: str) -> tuple[bool | None, str, str]:
    dotenv_path = get_dotenv_path()
    return dotenv.set_key(dotenv_path, key, value)


def load_dotenv() -> bool:
    dotenv_path = get_dotenv_path()
    return dotenv.load_dotenv(dotenv_path)


def get_cache_dir() -> Path:
    return Path(user_cache_dir("kabukit"))
