from __future__ import annotations

import pytest

from govflow_backend.core.config import GovFlowSettings, get_settings


def test_get_settings_type_and_cors_parsing() -> None:
    s = get_settings()
    assert isinstance(s, GovFlowSettings)
    assert "http://localhost:5173" in s.backend_cors_origins


def test_security_trusted_hosts_csv_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOVFLOW_SECURITY_TRUSTED_HOSTS", "example.com, *.example.org")
    get_settings.cache_clear()
    hosts = get_settings().security_trusted_hosts
    assert hosts == ["example.com", "*.example.org"]
