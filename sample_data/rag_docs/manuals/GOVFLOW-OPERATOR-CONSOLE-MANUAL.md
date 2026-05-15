# GovFlow AI — Operator console manual *(synthetic demo document)*

## 1. Introduction

The **GovFlow AI** operator console is a read-heavy dashboard for monitoring API health, optional agent snapshots, and retrieval-augmented generation (RAG) checks against an indexed Markdown corpus.

## 2. Roles

| Role | Capabilities |
| --- | --- |
| Viewer | Read health, run canned RAG queries |
| Operator | Invoke workflow simulator presets, review guardrail summaries |
| Administrator | Configure environment variables, rotate API keys, manage ingestion |

## 3. Routine checks

1. Confirm **liveness** and **readiness** endpoints return `ok`.  
2. Run **agent snapshot** refresh to validate LangGraph wiring.  
3. Execute a **RAG quick check** with a question known to exist in the corpus to validate embeddings and vector store persistence.

## 4. Escalation

If readiness reports a missing sample data directory, verify `GOVFLOW_SAMPLE_DATA_DIR` and volume mounts in container deployments.
