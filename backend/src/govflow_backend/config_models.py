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


class AppSectionModel(BaseModel):
    name: str
    description: str
    api: ApiConfigModel
    cors: CorsConfigModel
    graph: GraphYamlConfig


class FeaturesModel(BaseModel):
    llm_enabled: bool
    graph_persistence_enabled: bool


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
