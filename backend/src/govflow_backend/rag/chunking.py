"""Text splitting strategies from YAML."""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from govflow_backend.rag.schema import ChunkingConfig


def build_recursive_splitter(cfg: ChunkingConfig) -> RecursiveCharacterTextSplitter:
    kwargs: dict = {
        "chunk_size": cfg.chunk_size,
        "chunk_overlap": cfg.chunk_overlap,
    }
    if cfg.separators:
        kwargs["separators"] = cfg.separators
    return RecursiveCharacterTextSplitter(**kwargs)


def split_rag_documents(
    *,
    documents: list[Document],
    splitter: RecursiveCharacterTextSplitter,
) -> list[Document]:
    return splitter.split_documents(documents)
