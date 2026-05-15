from __future__ import annotations

from fastapi.testclient import TestClient

from govflow_backend.main import app


def test_health_live() -> None:
    with TestClient(app) as client:
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_health_ready() -> None:
    with TestClient(app) as client:
        response = client.get("/health/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["environment"] == "development"
        assert "sample_data_dir_exists" in body
