from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from govflow_backend.main import app


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


def test_graph_invoke_returns_observability(client: TestClient) -> None:
    response = client.post(
        "/v1/graph/invoke",
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert data["messages"]
    assert "observability" in data
    assert "totals" in data["observability"]


def test_graph_stream_sse_done_event(client: TestClient) -> None:
    with client.stream(
        "POST",
        "/v1/graph/stream",
        json={"messages": [{"role": "user", "content": "Stream test"}]},
    ) as response:
        assert response.status_code == 200
        raw = "".join(response.iter_text())
    lines = [ln for ln in raw.splitlines() if ln.startswith("data: ")]
    assert lines
    last_payload = json.loads(lines[-1].removeprefix("data: "))
    assert last_payload.get("done") is True
    assert "observability" in last_payload
