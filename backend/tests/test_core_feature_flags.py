from __future__ import annotations

from types import SimpleNamespace

from govflow_backend.config_models import FeaturesModel
from govflow_backend.core.feature_flags import resolve_effective_feature_flags


def test_resolve_honors_env_overrides_when_set() -> None:
    features = FeaturesModel(
        llm_enabled=False,
        graph_persistence_enabled=False,
        rag_api_enabled=True,
        graph_api_enabled=False,
    )
    settings = SimpleNamespace(
        feature_rag_api_enabled=False,
        feature_graph_api_enabled=True,
    )
    flags = resolve_effective_feature_flags(settings, features)
    assert flags.rag_api_enabled is False
    assert flags.graph_api_enabled is True


def test_resolve_falls_back_to_yaml_when_env_unset() -> None:
    features = FeaturesModel(
        llm_enabled=False,
        graph_persistence_enabled=False,
        rag_api_enabled=False,
        graph_api_enabled=True,
    )
    settings = SimpleNamespace(
        feature_rag_api_enabled=None,
        feature_graph_api_enabled=None,
    )
    flags = resolve_effective_feature_flags(settings, features)
    assert flags.rag_api_enabled is False
    assert flags.graph_api_enabled is True
