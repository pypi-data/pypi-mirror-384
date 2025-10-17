"""Configuration management utilities.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import os
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path.home() / ".aip"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


def load_config() -> dict[str, Any]:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return {}

    try:
        with open(CONFIG_FILE) as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError:
        return {}


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to file."""
    CONFIG_DIR.mkdir(exist_ok=True)

    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    # Set secure file permissions
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except (
        OSError
    ):  # pragma: no cover - permission errors are expected in some environments
        pass
