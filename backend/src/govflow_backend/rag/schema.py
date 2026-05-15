"""Pydantic schema for `config/rag*.yaml` (includes prompts — no secrets)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChunkingConfig(BaseModel):
    strategy: Literal["recursive_character"] = "recursive_character"
    chunk_size: int = Field(ge=32, le=100_000)
    chunk_overlap: int = Field(ge=0, le=50_000)
    separators: list[str] | None = None


class EmbeddingsYamlConfig(BaseModel):
    provider: Literal["openai", "fake"] = "openai"


class RetrievalConfig(BaseModel):
    default_top_k: int = Field(ge=1, le=100)
    score_threshold: float | None = None
    max_chunks_for_prompt: int = Field(ge=1, le=50)


class LoaderEntryYaml(BaseModel):
    type: Literal["markdown_directory", "text_file"]
    path_env_key: str
    glob_pattern: str = "**/*.md"


class IngestionConfigYaml(BaseModel):
    loaders: list[LoaderEntryYaml] = Field(default_factory=list)


class QaConfigYaml(BaseModel):
    mode: Literal["extractive", "generative"] = "extractive"
    min_grounding_score: float = Field(ge=0.0, le=1.0)
    require_citation_brackets: bool = True


class PromptsYaml(BaseModel):
    generative_system: str
    generative_user: str
    hallucination_check_user: str


class RagYamlRoot(BaseModel):
    chunking: ChunkingConfig
    embeddings: EmbeddingsYamlConfig
    retrieval: RetrievalConfig
    ingestion: IngestionConfigYaml
    qa: QaConfigYaml
    prompts: PromptsYaml


class ScoredChunk(BaseModel):
    model_config = {"extra": "ignore"}

    chunk_id: str
    content: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)
