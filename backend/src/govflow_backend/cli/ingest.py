"""CLI entrypoint for document ingestion."""

from __future__ import annotations

import logging

import typer

from govflow_backend.config_loader import load_merged_file_config
from govflow_backend.core.config import get_settings
from govflow_backend.core.logging import setup_logging
from govflow_backend.rag.factories import build_rag_runtime
from govflow_backend.rag.yaml_loader import load_rag_config


def ingest_run(
    reset: bool = typer.Option(
        False,
        "--reset",
        help="Delete existing vectors for the configured collection before ingesting.",
    ),
) -> None:
    """Load documents from configured loaders, chunk, embed, and upsert into the vector store."""

    settings = get_settings()
    file_cfg = load_merged_file_config(
        config_dir=settings.resolved_config_dir,
        environment=settings.environment,
    )
    setup_logging(settings, file_cfg)
    logging.getLogger("chromadb").setLevel(logging.WARNING)

    rag_yaml = load_rag_config(
        config_dir=settings.resolved_config_dir, environment=settings.environment
    )
    runtime = build_rag_runtime(settings, rag_yaml)
    result = runtime.ingestion.ingest(reset=reset)
    msg = (
        f"Ingestion complete: documents_loaded={result.documents_loaded} "
        f"chunks_indexed={result.chunks_indexed}"
    )
    typer.echo(msg)


def main() -> None:
    typer.run(ingest_run)


if __name__ == "__main__":
    main()
