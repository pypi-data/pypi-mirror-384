from __future__ import annotations

import os
import tomllib
from pathlib import Path

import toml
from platformdirs import user_cache_dir, user_config_dir


def get_cache_dir() -> Path:
    """Return the absolute path to the user-specific cache directory for 'kabukit'.

    This directory is used for storing temporary data or cached information
    related to the application.

    Returns:
        Path: The path to the cache directory.
    """
    return Path(user_cache_dir("kabukit"))


def get_config_path() -> Path:
    """Return the path to the 'config.toml' file in the user's config directory.

    If the configuration directory does not exist, it will be created.

    Returns:
        Path: The path to the 'config.toml' file.
    """
    config_dir = Path(user_config_dir("kabukit"))
    config_dir.mkdir(parents=True, exist_ok=True)

    return config_dir / "config.toml"


def load_config() -> dict[str, str]:
    """Load the configuration settings from the 'config.toml' file.

    If the 'config.toml' file does not exist, an empty dictionary is returned.

    Returns:
        dict[str, str]: A dictionary containing the loaded configuration settings.
        Keys and values are expected to be strings.
    """
    config_path = get_config_path()

    if not config_path.exists():
        return {}

    with config_path.open("rb") as f:
        return tomllib.load(f)


def save_config_key(key: str, value: str, /) -> None:
    """Save a specific key-value pair to the 'config.toml' file.

    This function loads the existing configuration, updates or adds the specified
    key-value pair, and then writes the entire updated configuration back to the file.
    Existing comments and formatting in the 'config.toml' file may not be preserved.

    Args:
        key (str): The configuration key to set.
        value (str): The string value to associate with the key.
    """
    config_path = get_config_path()
    config = load_config()
    config[key] = value

    with config_path.open("w", encoding="utf-8") as f:
        toml.dump(config, f)


def get_config_value(key: str, /) -> str | None:
    """Retrieve a configuration value by key.

    First, it attempts to load the value from the 'config.toml' file.
    If the key is not found in the file, it then checks the environment
    variables.

    Args:
        key (str): The configuration key to retrieve.

    Returns:
        str | None: The string value associated with the key, or None
        if the key is not found in either the config file or environment
        variables.
    """
    config = load_config()

    return config.get(key, os.environ.get(key))
