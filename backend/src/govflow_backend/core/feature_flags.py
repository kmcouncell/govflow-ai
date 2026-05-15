"""Resolved feature flags (YAML + optional environment overrides)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from govflow_backend.config_models import FeaturesModel


class FeatureFlagEnv(Protocol):
    feature_rag_api_enabled: bool | None
    feature_graph_api_enabled: bool | None


@dataclass(frozen=True, slots=True)
class EffectiveFeatureFlags:
    rag_api_enabled: bool
    graph_api_enabled: bool


def resolve_effective_feature_flags(
    settings: FeatureFlagEnv,
    features: FeaturesModel,
) -> EffectiveFeatureFlags:
    rag = (
        settings.feature_rag_api_enabled
        if settings.feature_rag_api_enabled is not None
        else features.rag_api_enabled
    )
    graph = (
        settings.feature_graph_api_enabled
        if settings.feature_graph_api_enabled is not None
        else features.graph_api_enabled
    )
    return EffectiveFeatureFlags(rag_api_enabled=rag, graph_api_enabled=graph)
