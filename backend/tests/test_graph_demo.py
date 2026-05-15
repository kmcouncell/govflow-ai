from __future__ import annotations

from fastapi.testclient import TestClient

from govflow_backend.main import app


def test_graph_demo_degraded_mode() -> None:
    with TestClient(app) as client:
        response = client.post("/v1/graph/demo")
        assert response.status_code == 200
        payload = response.json()["result"]
        assert "messages" in payload
        assert payload["messages"]
