from __future__ import annotations

from fastapi.testclient import TestClient

from govflow_backend.main import app


def test_openapi_schema_contains_documented_paths_and_tags() -> None:
    with TestClient(app) as client:
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()

    paths = schema["paths"]
    assert "/health/live" in paths
    assert "/v1/graph/invoke" in paths
    assert "/v1/rag/query" in paths

    tags = {t["name"] for t in schema.get("tags", [])}
    assert {"health", "graph", "rag"}.issubset(tags)

    invoke_schema = paths["/v1/graph/invoke"]["post"]
    assert "requestBody" in invoke_schema

    rag_schema = paths["/v1/rag/query"]["post"]
    assert "requestBody" in rag_schema


def test_openapi_info_description_is_non_empty() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()
    assert isinstance(schema["info"].get("description", ""), str)
    assert len(schema["info"]["description"]) > 50
