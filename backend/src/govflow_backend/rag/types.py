"""Runtime RAG document types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RagDocument:
    """Logical document prior to embedding."""

    doc_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
