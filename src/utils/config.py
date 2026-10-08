"""Load settings relative to the project, independent of the working directory."""

import os
from pathlib import Path
from typing import Any
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "config.yaml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate the common configuration without creating directories."""
    config_path = Path(path).resolve() if path is not None else DEFAULT_CONFIG
    with config_path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a YAML mapping.")
    required = ("project", "paths", "data", "menu", "materials", "recipes")
    for key in required:
        if key not in config:
            raise ValueError(f"Missing configuration section: {key}")
    fractions = config["validation"]
    if (
        abs(
            sum(fractions[k] for k in ("train_fraction", "validation_fraction", "test_fraction"))
            - 1
        )
        > 1e-9
    ):
        raise ValueError("Time split fractions must sum to one.")
    if set(config["recipes"]) != set(config["menu"]):
        raise ValueError("Every menu item must have exactly one recipe.")
    for item, recipe in config["recipes"].items():
        for material, quantity in recipe.items():
            if material not in config["materials"] or quantity <= 0:
                raise ValueError(f"Invalid recipe entry: {item}/{material}")
    return config


def resolve_path(config: dict[str, Any], key: str) -> Path:
    """Resolve configured paths against the project root, not the shell directory."""
    path = Path(config["paths"][key])
    settings = config.get("sqlite", {})
    if key in ("database", "truth_database") and settings.get("honor_environment_override", True):
        directory = os.environ.get(settings.get("directory_env_variable", "COFFEE_DB_DIR"))
        if directory:
            location = Path(directory).expanduser()
            location = location if location.is_absolute() else PROJECT_ROOT / location
            return (location / path.name).resolve()
    return path if path.is_absolute() else PROJECT_ROOT / path
