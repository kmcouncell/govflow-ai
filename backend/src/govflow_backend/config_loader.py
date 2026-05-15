"""Load and deep-merge YAML configuration from a configurable directory."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml
from pydantic import TypeAdapter

from govflow_backend.config_models import AppYamlRoot, LoggingYamlRoot, MergedFileConfig
from govflow_backend.exceptions import ConfigurationError


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ConfigurationError(f"Configuration file not found: {path}")
    raw = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:  # pragma: no cover - exercised via corrupt file test if added
        raise ConfigurationError(f"Invalid YAML: {path}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigurationError(f"YAML root must be a mapping: {path}")
    return data


def load_merged_file_config(*, config_dir: Path, environment: str) -> MergedFileConfig:
    """Merge default YAML with environment-specific overlays."""
    default_app = config_dir / "app.default.yaml"
    env_app = config_dir / f"app.{environment}.yaml"
    default_log = config_dir / "logging.default.yaml"
    env_log = config_dir / f"logging.{environment}.yaml"

    merged_app: dict[str, Any] = _read_yaml(default_app)
    if env_app.is_file():
        merged_app = _deep_merge(merged_app, _read_yaml(env_app))

    merged_log = _read_yaml(default_log)
    if env_log.is_file():
        merged_log = _deep_merge(merged_log, _read_yaml(env_log))

    app_model = TypeAdapter(AppYamlRoot).validate_python(merged_app)
    log_model = TypeAdapter(LoggingYamlRoot).validate_python(merged_log)

    return MergedFileConfig(
        app=app_model.app,
        features=app_model.features,
        logging=log_model.logging,
    )
