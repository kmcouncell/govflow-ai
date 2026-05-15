"""Citation formatting and lightweight hallucination heuristics."""

from __future__ import annotations

import re

from govflow_backend.rag.schema import ScoredChunk


def format_numbered_excerpts(chunks: list[ScoredChunk]) -> str:
    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(f"[{i}] {chunk.content.strip()}")
    return "\n\n".join(parts)


def citation_indices(answer: str) -> list[int]:
    found = {int(m.group(1)) for m in re.finditer(r"\[(\d+)\]", answer)}
    return sorted(found)


def lexical_grounding_score(answer: str, sources: list[str]) -> float:
    tokens = [t for t in re.findall(r"\w+", answer.lower()) if len(t) > 2]
    if not tokens:
        return 0.0
    blob = " ".join(sources).lower()
    unique = set(tokens)
    hits = sum(1 for t in unique if t in blob)
    return min(1.0, hits / max(1, len(unique)))


def possible_hallucination(score: float, threshold: float) -> bool:
    return score < threshold
