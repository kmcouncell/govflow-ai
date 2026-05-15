"""Resolve OpenAI-compatible chat model names from env and YAML (no hard-coded model IDs)."""

from __future__ import annotations

from govflow_backend.config_models import MergedFileConfig
from govflow_backend.core.config import GovFlowSettings


def resolve_openai_chat_model(settings: GovFlowSettings, file_config: MergedFileConfig) -> str:
    """Return the chat model id: explicit env wins, otherwise YAML default."""

    explicit = (settings.openai_model or "").strip()
    if explicit:
        return explicit
    return file_config.app.llm.default_chat_model.strip()
