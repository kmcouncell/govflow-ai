"""Pluggable document loaders driven by YAML + environment paths."""

from __future__ import annotations

import os
from pathlib import Path

from govflow_backend.core.logging import get_logger
from govflow_backend.exceptions import RagError
from govflow_backend.rag.schema import IngestionConfigYaml
from govflow_backend.rag.types import RagDocument

log = get_logger(__name__)


def _load_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_markdown_directory(root: Path, glob_pattern: str) -> list[RagDocument]:
    if not root.is_dir():
        raise RagError(f"RAG loader root is not a directory: {root}")
    documents: list[RagDocument] = []
    for path in sorted(root.glob(glob_pattern)):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root))
        documents.append(
            RagDocument(
                doc_id=f"file:{rel}",
                content=_load_text_file(path),
                metadata={
                    "source": rel,
                    "loader": "markdown_directory",
                    "absolute_path": str(path.resolve()),
                },
            ),
        )
    return documents


def _load_single_text_file(path: Path) -> list[RagDocument]:
    if not path.is_file():
        raise RagError(f"RAG loader path is not a file: {path}")
    return [
        RagDocument(
            doc_id=f"file:{path.name}",
            content=_load_text_file(path),
            metadata={
                "source": path.name,
                "loader": "text_file",
                "absolute_path": str(path.resolve()),
            },
        ),
    ]


def load_raw_documents(ingestion: IngestionConfigYaml) -> list[RagDocument]:
    """Resolve each loader entry using `os.environ[path_env_key]`."""

    all_docs: list[RagDocument] = []
    for entry in ingestion.loaders:
        raw_path = os.environ.get(entry.path_env_key, "").strip()
        if not raw_path:
            log.warning(
                "rag_loader_skipped_missing_env",
                path_env_key=entry.path_env_key,
                loader_type=entry.type,
            )
            continue
        path = Path(raw_path).expanduser().resolve()
        if entry.type == "markdown_directory":
            all_docs.extend(_load_markdown_directory(path, entry.glob_pattern))
        elif entry.type == "text_file":
            all_docs.extend(_load_single_text_file(path))
        else:  # pragma: no cover - validated by pydantic
            raise RagError(f"Unsupported loader type: {entry.type}")
    return all_docs
