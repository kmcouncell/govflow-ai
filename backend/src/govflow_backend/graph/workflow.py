"""LangGraph application graph wiring."""

from __future__ import annotations

from govflow_backend.agents.graph import build_supervisor_graph

# Backwards-compatible alias used by early bootstrap code/tests.
build_stub_graph = build_supervisor_graph

__all__ = ["build_stub_graph", "build_supervisor_graph"]
