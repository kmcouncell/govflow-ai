"""Load merged agent prompt YAML from `config/prompts/`."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml
from pydantic import TypeAdapter

from govflow_backend.agents.schema import AgentsPromptYaml
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
        raise ConfigurationError(f"Agent prompts file not found: {path}")
    raw = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Invalid agent prompts YAML: {path}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigurationError(f"Agent prompts YAML root must be a mapping: {path}")
    return data


def load_agents_prompt_config(*, config_dir: Path, environment: str) -> AgentsPromptYaml:
    prompts_dir = config_dir / "prompts"
    default_path = prompts_dir / "agents.default.yaml"
    overlay_path = prompts_dir / f"agents.{environment}.yaml"

    merged = _read_yaml(default_path)
    if overlay_path.is_file():
        merged = _deep_merge(merged, _read_yaml(overlay_path))

    return TypeAdapter(AgentsPromptYaml).validate_python(merged)
