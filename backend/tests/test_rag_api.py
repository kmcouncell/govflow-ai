from __future__ import annotations

from fastapi.testclient import TestClient

from govflow_backend.main import create_app


def test_rag_ingest_and_query_end_to_end() -> None:
    with TestClient(create_app()) as client:
        ingest = client.post("/v1/rag/ingest", json={"reset": True})
        assert ingest.status_code == 200, ingest.text
        payload = ingest.json()
        assert payload["documents_loaded"] >= 1
        assert payload["chunks_indexed"] >= 1

        query = client.post(
            "/v1/rag/query",
            json={
                "question": "What does RAG stand for?",
                "metadata_filter": {"source": "kb.md"},
                "top_k": 4,
            },
        )
        assert query.status_code == 200, query.text
        body = query.json()
        assert "answer" in body
        assert "citations" in body
        assert "grounding_score" in body
        assert "possible_hallucination" in body
        assert isinstance(body["retrieved"], list)
        assert body["retrieved"], "expected non-empty retrieval"


def test_rag_ingest_validation_error() -> None:
    with TestClient(create_app()) as client:
        bad = client.post("/v1/rag/query", json={"question": ""})
        assert bad.status_code == 422
