"""High-level orchestration service combining search and synthesis."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.services.llm_service import LLMManager
from src.services.paper_service import OpenAlexClient
from src.services.performance_service.rust_performance import HighPerformanceService
from src.services.research_service.enhanced_synthesizer import EnhancedSynthesizer
from src.services.search_service import SearchEngine

logger = logging.getLogger(__name__)


class EnhancedResearchService:
    """Bundle search + synthesis into a cohesive workflow."""

    def __init__(
        self,
        *,
        search_engine: Optional[SearchEngine] = None,
        synthesizer: Optional[EnhancedSynthesizer] = None,
        llm_manager: Optional[LLMManager] = None,
        openalex_client: Optional[OpenAlexClient] = None,
        performance_service: Optional[HighPerformanceService] = None,
    ) -> None:
        self.openalex = openalex_client or OpenAlexClient()
        self.llm = llm_manager or LLMManager()
        self.performance = performance_service or HighPerformanceService()
        self.search_engine = search_engine or SearchEngine(
            openalex_client=self.openalex,
            performance_service=self.performance,
        )
        self.synthesizer = synthesizer or EnhancedSynthesizer(
            llm_manager=self.llm,
            openalex_client=self.openalex,
            performance_service=self.performance,
        )

    async def conduct_research(
        self,
        query: str,
        *,
        limit: int = 10,
        max_words: int = 600,
        style: str = "comprehensive",
        include_advanced: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not query or not query.strip():
            raise ValueError("Query must be a non-empty string")

        context = context or {}
        context.setdefault("original_query", query)

        search_payload = await self.search_engine.search_papers(
            query,
            limit=limit,
            sources=("openalex", "pubmed") if include_advanced else ("openalex",),
            include_metadata=True,
            include_abstracts=True,
        )

        paper_ids = [paper["id"] for paper in search_payload.get("papers", [])]
        raw_papers: List[Dict[str, Any]] = []
        if paper_ids:
            raw_papers = await self.openalex.get_papers_bulk(paper_ids)

        if not raw_papers:
            # Fall back to lightly formatted payloads if bulk fetch fails
            raw_papers = [self._paper_stub(paper) for paper in search_payload.get("papers", [])]

        synthesis = await self.synthesizer.synthesize_research(
            papers=raw_papers,
            max_words=max_words,
            style=style,
            context=context,
            include_visualizations=True,
            include_topic_modeling=True,
            include_quality_assessment=True,
        )

        return {
            "query": query,
            "search": search_payload,
            "synthesis": synthesis,
        }

    async def get_health_status(self) -> Dict[str, Any]:
        search_stats = {
            "openalex": True,
            "web_search": True,
        }
        try:
            kg_stats = await self.synthesizer.kg.stats()
        except Exception as exc:  # pragma: no cover - KG optional
            logger.info("Knowledge graph stats unavailable", extra={"error": str(exc)})
            kg_stats = {"entities": 0, "relationships": 0}

        llm_health = await self.llm.health_check()
        return {
            "search": search_stats,
            "knowledge_graph": kg_stats,
            "llm": llm_health,
        }

    def _paper_stub(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": payload.get("id"),
            "title": payload.get("title"),
            "abstract": payload.get("abstract", ""),
            "authors": payload.get("authors", []),
            "publication_year": payload.get("year"),
            "doi": payload.get("doi"),
            "concepts": [{"display_name": kw} for kw in payload.get("keywords", [])],
        }


__all__ = ["EnhancedResearchService"]
