# Sample data

Non-sensitive **synthetic** federal-style materials for demos, RAG grounding, and local testing.

## Layout

| Path | Format | Purpose |
| --- | --- | --- |
| `rag_docs/` | Markdown (`**/*.md`) | Default ingestion corpus (`GOVFLOW_RAG_SOURCE_DIR`); includes `policies/`, `manuals/`, and `workflows/` |
| `policies/pdf/` | PDF | Companion policy excerpts for UI/download demos (not loaded by default Markdown RAG loader) |

## Regenerating PDFs

From the repository root:

```bash
cd backend && uv run --with fpdf2 python ../scripts/generate_sample_pdfs.py
```

## Configuration

Paths are controlled by `GOVFLOW_SAMPLE_DATA_DIR` and `GOVFLOW_RAG_SOURCE_DIR` (see root `.env.example`).
