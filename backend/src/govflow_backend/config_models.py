"""Pydantic models for YAML-backed configuration (no secrets)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ApiConfigModel(BaseModel):
    title: str
    version: str
    docs_enabled: bool
    openapi_url: str


class CorsConfigModel(BaseModel):
    allow_credentials: bool
    allow_methods: list[str]
    allow_headers: list[str]


class GraphYamlConfig(BaseModel):
    default_thread_ttl_seconds: int = Field(ge=1)
    max_steps: int = Field(ge=1)


class LlmYamlConfig(BaseModel):
    """Defaults when `GOVFLOW_OPENAI_MODEL` is unset (non-secret; tune per environment)."""

    default_chat_model: str = Field(
        min_length=1,
        max_length=128,
        description="Chat model id when GOVFLOW_OPENAI_MODEL is unset.",
    )


class AppSectionModel(BaseModel):
    name: str
    description: str
    api: ApiConfigModel
    cors: CorsConfigModel
    graph: GraphYamlConfig
    llm: LlmYamlConfig


class FeaturesModel(BaseModel):
    llm_enabled: bool
    graph_persistence_enabled: bool
    rag_api_enabled: bool = True
    graph_api_enabled: bool = True


class AppYamlRoot(BaseModel):
    app: AppSectionModel
    features: FeaturesModel


class LoggingYamlRoot(BaseModel):
    logging: dict[str, Any]


class MergedFileConfig(BaseModel):
    """Validated merge of default + environment YAML layers."""

    app: AppSectionModel
    features: FeaturesModel
    logging: dict[str, Any]
