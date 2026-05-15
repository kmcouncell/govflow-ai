"""Question answering with YAML prompts and citation-aware guardrails."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from govflow_backend.core.config import GovFlowSettings
from govflow_backend.exceptions import RagError
from govflow_backend.rag.guardrails import (
    citation_indices,
    format_numbered_excerpts,
    lexical_grounding_score,
    possible_hallucination,
)
from govflow_backend.rag.retrieval import Retriever
from govflow_backend.rag.schema import RagYamlRoot, ScoredChunk


@dataclass(slots=True)
class QaResult:
    answer: str
    citations: list[int]
    grounding_score: float
    possible_hallucination: bool
    retrieved: list[ScoredChunk]

    def model_dump(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["retrieved"] = [c.model_dump() for c in self.retrieved]
        return payload


class QaService:
    def __init__(
        self, *, settings: GovFlowSettings, rag_yaml: RagYamlRoot, retriever: Retriever
    ) -> None:
        self._settings = settings
        self._rag_yaml = rag_yaml
        self._retriever = retriever

    def answer(
        self,
        *,
        question: str,
        metadata_filter: dict[str, Any] | None,
        top_k: int | None,
    ) -> QaResult:
        chunks = self._retriever.retrieve(
            query=question,
            metadata_filter=metadata_filter,
            top_k=top_k,
        )
        max_n = self._rag_yaml.retrieval.max_chunks_for_prompt
        excerpts = chunks[:max_n]

        if self._rag_yaml.qa.mode == "extractive":
            answer = self._answer_extractive(excerpts, question)
        else:
            answer = self._answer_generative(excerpts, question)

        sources = [c.content for c in excerpts]
        score = lexical_grounding_score(answer, sources)
        cites = citation_indices(answer) if self._rag_yaml.qa.require_citation_brackets else []
        flagged = possible_hallucination(score, self._rag_yaml.qa.min_grounding_score)
        return QaResult(
            answer=answer,
            citations=cites,
            grounding_score=score,
            possible_hallucination=flagged,
            retrieved=chunks,
        )

    def _answer_extractive(self, excerpts: list[ScoredChunk], question: str) -> str:
        if not excerpts:
            return "I do not have matching sources in the knowledge base for this question."
        lead = excerpts[0].content.strip()
        return f"Based on the indexed sources, the closest excerpt is [1]: {lead}"

    def _answer_generative(self, excerpts: list[ScoredChunk], question: str) -> str:
        if not self._settings.openai_api_key:
            raise RagError("Generative QA requires GOVFLOW_OPENAI_API_KEY")
        if not excerpts:
            return "I do not have matching sources in the knowledge base for this question."

        prompts = self._rag_yaml.prompts
        context_block = format_numbered_excerpts(excerpts)
        user_prompt = prompts.generative_user.format(
            context_excerpts=context_block,
            question=question,
        )

        kwargs: dict[str, Any] = {
            "model": self._settings.openai_model or "gpt-4o-mini",
            "temperature": 0.0,
            "api_key": self._settings.openai_api_key,
        }
        if self._settings.openai_base_url:
            kwargs["base_url"] = self._settings.openai_base_url

        llm = ChatOpenAI(**kwargs)
        messages = [
            SystemMessage(content=prompts.generative_system),
            HumanMessage(content=user_prompt),
        ]
        response = llm.invoke(messages)
        content = response.content
        if isinstance(content, list):
            text = "".join(str(part) for part in content)
        else:
            text = str(content)
        return text.strip()
