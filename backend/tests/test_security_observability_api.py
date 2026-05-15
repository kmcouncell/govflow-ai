from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient

from govflow_backend.core.rate_limit import reset_rate_limit_counters
from govflow_backend.main import app


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


def test_ai_route_exposes_duration_headers(client: TestClient) -> None:
    r = client.post("/v1/graph/demo")
    assert r.status_code == 200
    assert "X-Govflow-Request-Duration-Ms" in r.headers
    assert "X-Govflow-AI-Route-Latency-Ms" in r.headers


def test_graph_invoke_includes_guardrails_summary(client: TestClient) -> None:
    r = client.post("/v1/graph/invoke", json={"messages": [{"role": "user", "content": "Hello"}]})
    assert r.status_code == 200
    body = r.json()
    assert "guardrails" in body
    assert "request_latency_ms" in body


def test_audit_log_emitted(caplog: pytest.LogCaptureFixture, client: TestClient) -> None:
    caplog.set_level(logging.INFO, logger="govflow_backend.ai_audit")
    client.post("/v1/graph/demo")
    assert any("ai_interaction" in r.message for r in caplog.records)


def test_rate_limit_tight(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    reset_rate_limit_counters()
    ra = app.state.responsible_ai.model_copy(
        update={
            "rate_limiting": app.state.responsible_ai.rate_limiting.model_copy(
                update={
                    "enabled": True,
                    "window_seconds": 60,
                    "ai_route_requests_per_window": 1,
                    "default_requests_per_window": 1000,
                },
            ),
        },
    )
    monkeypatch.setattr(app.state, "responsible_ai", ra, raising=False)
    try:
        assert client.post("/v1/graph/demo").status_code == 200
        assert client.post("/v1/graph/demo").status_code == 429
    finally:
        reset_rate_limit_counters()


def test_guardrails_violation_returns_400(client: TestClient) -> None:
    ra = app.state.responsible_ai
    bad = ra.model_copy(
        update={
            "guardrails": ra.guardrails.model_copy(
                update={
                    "input_validation": ra.guardrails.input_validation.model_copy(
                        update={"blocked_regex": [r"(?i)forbidden_token"]},
                    ),
                },
            ),
        },
    )
    app.state.responsible_ai = bad
    try:
        r = client.post(
            "/v1/graph/invoke",
            json={"messages": [{"role": "user", "content": "forbidden_token in input"}]},
        )
        assert r.status_code == 400
        assert r.json().get("detail") == "guardrails_violation"
    finally:
        app.state.responsible_ai = ra
