from __future__ import annotations

from govflow_backend.rag.guardrails import (
    citation_indices,
    lexical_grounding_score,
    possible_hallucination,
)
from govflow_backend.rag.schema import ScoredChunk


def test_citation_indices_parsed() -> None:
    assert citation_indices("See [1] and also [3] for details.") == [1, 3]


def test_lexical_grounding_and_hallucination_flag() -> None:
    sources = ["The quick brown fox jumps over the lazy dog."]
    answer = "The quick brown fox appears in the excerpt [1]."
    score = lexical_grounding_score(answer, sources)
    assert score > 0.4
    assert possible_hallucination(score, threshold=0.12) is False

    weak = "Completely unrelated zyzzyx qwerty nonsense."
    low = lexical_grounding_score(weak, sources)
    assert possible_hallucination(low, threshold=0.12) is True


def test_scored_chunk_model_dump() -> None:
    c = ScoredChunk(chunk_id="1", content="x", score=0.9, metadata={"k": "v"})
    d = c.model_dump()
    assert d["chunk_id"] == "1"
