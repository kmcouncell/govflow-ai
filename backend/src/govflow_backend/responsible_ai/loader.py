"""Load merged responsible AI YAML."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml
from pydantic import TypeAdapter

from govflow_backend.exceptions import ConfigurationError
from govflow_backend.responsible_ai.schema import ResponsibleAiYaml


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
        raise ConfigurationError(f"Responsible AI configuration not found: {path}")
    raw = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Invalid responsible AI YAML: {path}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigurationError(f"Responsible AI YAML root must be a mapping: {path}")
    return data


def load_responsible_ai_config(*, config_dir: Path, environment: str) -> ResponsibleAiYaml:
    default_path = config_dir / "responsible_ai.default.yaml"
    overlay_path = config_dir / f"responsible_ai.{environment}.yaml"

    merged = _read_yaml(default_path)
    if overlay_path.is_file():
        merged = _deep_merge(merged, _read_yaml(overlay_path))

    return TypeAdapter(ResponsibleAiYaml).validate_python(merged)
