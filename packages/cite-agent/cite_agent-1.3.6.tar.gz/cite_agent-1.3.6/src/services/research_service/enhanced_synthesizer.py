"""Advanced research synthesiser used by the SophisticatedResearchEngine."""

from __future__ import annotations

import asyncio
import logging
import math
import statistics
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from src.services.graph.knowledge_graph import KnowledgeGraph
from src.services.llm_service import LLMManager
from src.services.paper_service import OpenAlexClient
from src.services.performance_service.rust_performance import HighPerformanceService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SynthesizerPaper:
    """Internal representation of a paper ready for synthesis."""

    paper_id: str
    title: str
    abstract: str
    year: Optional[int]
    doi: str
    authors: List[str]
    keywords: List[str]
    url: str
    fallback: bool = False

    def to_context_block(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.abstract,
            "authors": self.authors,
            "year": self.year,
            "keywords": self.keywords,
        }


class EnhancedSynthesizer:
    """High-fidelity synthesis engine with KG enrichment and telemetry."""

    def __init__(
        self,
        *,
        llm_manager: Optional[LLMManager] = None,
        openalex_client: Optional[OpenAlexClient] = None,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        performance_service: Optional[HighPerformanceService] = None,
        redis_url: Optional[str] = None,
    ) -> None:
        self.llm = llm_manager or LLMManager(redis_url=redis_url or "redis://localhost:6379")
        self.openalex = openalex_client or OpenAlexClient()
        self.kg = knowledge_graph or KnowledgeGraph()
        self.performance = performance_service or HighPerformanceService()
        self._cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._cache_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    async def synthesize_research(
        self,
        *,
        papers: Sequence[Dict[str, Any]],
        max_words: int = 500,
        style: str = "comprehensive",
        context: Optional[Dict[str, Any]] = None,
        include_visualizations: bool = True,
        include_topic_modeling: bool = True,
        include_quality_assessment: bool = True,
    ) -> Dict[str, Any]:
        """Produce an advanced synthesis result.

        Args:
            papers: Pre-fetched paper payloads (OpenAlex-compatible dictionaries).
            max_words: Target word count for the generated synthesis.
            style: Output style hint ("comprehensive", "executive", ...).
            context: Additional directives (focus areas, custom prompts, query).
        Returns:
            Rich synthesis dictionary consumed by the API layer.
        """

        context = context or {}
        focus_terms = context.get("focus") or context.get("custom_prompt") or ""
        trace_id = context.get("trace_id") or str(uuid.uuid4())

        normalized_papers = await self._prepare_papers(papers)
        cache_key = self._make_cache_key(normalized_papers, max_words, style, focus_terms)
        cached = await self._read_cache(cache_key)
        if cached is not None:
            cached["routing_metadata"]["cached"] = True
            cached["trace_id"] = trace_id
            return cached

        llm_prompt = self._build_prompt(len(normalized_papers), max_words, style, focus_terms)
        llm_context = [paper.to_context_block() for paper in normalized_papers]
        llm_result = await self.llm.generate_synthesis(llm_context, llm_prompt)
        summary_text = llm_result.get("summary", "")

        key_findings = self._extract_key_findings(summary_text, max_items=6)
        if include_topic_modeling:
            try:
                keywords = await self.performance.extract_keywords(summary_text, max_keywords=12)
            except Exception:
                keywords = self._fallback_keywords(summary_text)
        else:
            keywords = self._fallback_keywords(summary_text)

        citations = self._build_citations(normalized_papers)
        confidence = self._estimate_confidence(normalized_papers, summary_text, key_findings)
        domain_alignment = self._infer_domain(normalized_papers, focus_terms)
        relevance_score = self._score_relevance(summary_text, focus_terms or context.get("original_query", ""))

        metadata: Dict[str, Any] = {
            "keywords": keywords,
            "paper_sample_size": len(normalized_papers),
            "domain_alignment": domain_alignment,
            "confidence": confidence,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        if include_visualizations:
            metadata["visualizations"] = self._visualization_payload(normalized_papers)
        if include_quality_assessment:
            metadata["quality_assessment"] = self._quality_assessment(normalized_papers)

        await self._upsert_knowledge_graph(normalized_papers, key_findings)

        routing_metadata = {
            "routing_decision": {
                "model": llm_result.get("model"),
                "provider": llm_result.get("provider"),
                "complexity": "advanced",
                "strategy": "advanced_synthesizer",
            },
            "usage": llm_result.get("usage", {}),
            "latency": llm_result.get("latency"),
            "cached": llm_result.get("cached", False),
        }

        result = {
            "summary": summary_text,
            "word_count": len(summary_text.split()),
            "key_findings": key_findings,
            "citations_used": citations,
            "metadata": metadata,
            "routing_metadata": routing_metadata,
            "confidence": confidence,
            "relevance_score": relevance_score,
            "trace_id": trace_id,
        }

        await self._write_cache(cache_key, result)
        return result

    # ------------------------------------------------------------------
    async def _prepare_papers(self, raw_papers: Sequence[Dict[str, Any]]) -> List[SynthesizerPaper]:
        tasks = [self._normalize_single_paper(paper) for paper in raw_papers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        normalized: List[SynthesizerPaper] = []
        missing_ids: List[str] = []
        for entry, raw in zip(results, raw_papers):
            if isinstance(entry, SynthesizerPaper):
                normalized.append(entry)
            else:
                paper_id = str(raw.get("id") or raw.get("paper_id") or raw.get("doi") or uuid.uuid4())
                missing_ids.append(paper_id)
        if missing_ids:
            fetched = await self.openalex.get_papers_bulk(missing_ids)
            for payload in fetched:
                normalized.append(await self._normalize_single_paper(payload, allow_fetch=False))
        normalized = [paper for paper in normalized if paper.abstract]
        deduped: Dict[str, SynthesizerPaper] = {}
        for paper in normalized:
            deduped[paper.paper_id] = paper
        return list(deduped.values())

    async def _normalize_single_paper(self, payload: Dict[str, Any], *, allow_fetch: bool = True) -> SynthesizerPaper:
        paper_id = str(payload.get("id") or payload.get("paper_id") or payload.get("doi") or uuid.uuid4())
        title = payload.get("title") or payload.get("display_name") or f"Paper {paper_id}"
        abstract = self._extract_abstract(payload)
        if not abstract and allow_fetch:
            fetched = await self.openalex.get_paper_by_id(paper_id)
            return await self._normalize_single_paper(fetched or {"id": paper_id}, allow_fetch=False)
        doi = payload.get("doi", "").replace("https://doi.org/", "")
        authors = self._extract_authors(payload)
        keywords = self._extract_keywords(payload)
        url = payload.get("id") or payload.get("url") or f"https://openalex.org/{paper_id}"
        fallback = bool(payload.get("fallback"))
        return SynthesizerPaper(
            paper_id=paper_id,
            title=title,
            abstract=abstract,
            year=payload.get("publication_year") or payload.get("year"),
            doi=doi,
            authors=authors,
            keywords=keywords,
            url=url,
            fallback=fallback,
        )

    def _build_prompt(self, paper_count: int, max_words: int, style: str, focus: str) -> str:
        focus_clause = f"Focus on: {focus}." if focus else ""
        return (
            "Synthesise the following scholarly papers into a {style} briefing. "
            "Highlight methodological strengths, contradictions, effect sizes, and remaining research gaps. "
            "Return no more than {max_words} words. {focus_clause}"
        ).format(style=style, max_words=max_words, focus_clause=focus_clause)

    def _extract_key_findings(self, summary: str, *, max_items: int) -> List[str]:
        lines = [line.strip("-• ") for line in summary.splitlines() if line.strip()]
        findings: List[str] = []
        for line in lines:
            if len(findings) >= max_items:
                break
            if len(line.split()) < 6:
                continue
            if any(keyword in line.lower() for keyword in ("finding", "evidence", "increase", "decrease", "%")):
                findings.append(line)
            elif line.endswith("."):
                findings.append(line)
        if not findings:
            sentences = summary.split(". ")
            findings = [sentence.strip() for sentence in sentences[:max_items] if sentence.strip()]
        return findings

    def _build_citations(self, papers: Iterable[SynthesizerPaper]) -> Dict[str, str]:
        citations = {}
        for idx, paper in enumerate(papers, start=1):
            reference = paper.url or ("https://doi.org/" + paper.doi if paper.doi else paper.title)
            citations[f"[{idx}]"] = reference
        return citations

    def _estimate_confidence(self, papers: Sequence[SynthesizerPaper], summary: str, findings: Sequence[str]) -> float:
        fallback_penalty = 0.2 if any(paper.fallback for paper in papers) else 0.0
        diversity_bonus = min(0.3, math.log10(len(papers) + 1) / 2)
        finding_bonus = min(0.3, len(findings) / 10)
        length_penalty = 0.1 if len(summary.split()) < 150 else 0.0
        score = 0.5 + diversity_bonus + finding_bonus - fallback_penalty - length_penalty
        return max(0.1, min(0.99, round(score, 3)))

    def _infer_domain(self, papers: Sequence[SynthesizerPaper], focus: str) -> str:
        keywords = [kw.lower() for paper in papers for kw in paper.keywords]
        if focus:
            keywords.extend(focus.lower().split())
        if not keywords:
            return "general"
        if any(term in keywords for term in ("finance", "market", "equity", "stock")):
            return "quantitative_finance"
        if any(term in keywords for term in ("polymer", "resin", "manufacturing", "materials")):
            return "advanced_materials"
        if any(term in keywords for term in ("nlp", "language", "transformer", "model")):
            return "ai_research"
        return keywords[0][:32]

    def _score_relevance(self, summary: str, query: str) -> float:
        if not summary or not query:
            return 0.0
        summary_lower = summary.lower()
        tokens = {token for token in query.lower().split() if len(token) > 3}
        if not tokens:
            return 0.0
        matches = sum(1 for token in tokens if token in summary_lower)
        return round(matches / len(tokens), 3)

    def _visualization_payload(self, papers: Sequence[SynthesizerPaper]) -> Dict[str, Any]:
        years = [paper.year for paper in papers if paper.year]
        histogram: Dict[int, int] = {}
        for year in years:
            histogram[year] = histogram.get(year, 0) + 1
        return {
            "publication_histogram": histogram,
            "paper_urls": [paper.url for paper in papers],
        }

    def _quality_assessment(self, papers: Sequence[SynthesizerPaper]) -> Dict[str, Any]:
        citations = [paper for paper in papers if paper.doi]
        avg_year = statistics.mean([paper.year for paper in papers if paper.year] or [datetime.now().year])
        return {
            "avg_publication_year": round(avg_year, 1),
            "doi_coverage": round(len(citations) / max(1, len(papers)), 2),
            "sample_size": len(papers),
        }

    async def _upsert_knowledge_graph(self, papers: Sequence[SynthesizerPaper], findings: Sequence[str]) -> None:
        try:
            for paper in papers:
                entity_id = await self.kg.upsert_entity(
                    "Paper",
                    {
                        "id": paper.paper_id,
                        "title": paper.title,
                        "year": paper.year,
                        "doi": paper.doi,
                        "keywords": paper.keywords,
                    },
                )
                for author in paper.authors:
                    author_id = await self.kg.upsert_entity("Author", {"name": author})
                    await self.kg.upsert_relationship("authored", author_id, entity_id)
            for finding in findings:
                finding_id = await self.kg.upsert_entity("Finding", {"summary": finding})
                for paper in papers:
                    await self.kg.upsert_relationship("supports", paper.paper_id, finding_id)
        except Exception as exc:  # pragma: no cover - KG is best-effort
            logger.info("Knowledge graph enrichment failed", extra={"error": str(exc)})

    def _fallback_keywords(self, text: str) -> List[str]:
        import re
        from collections import Counter

        if not text:
            return []
        words = re.findall(r"[a-zA-Z]{4,}", text.lower())
        stop_words = {"this", "that", "with", "from", "into", "their", "which"}
        filtered = [word for word in words if word not in stop_words]
        return [word for word, _ in Counter(filtered).most_common(10)]

    def _extract_abstract(self, payload: Dict[str, Any]) -> str:
        inverted = payload.get("abstract_inverted_index")
        if isinstance(inverted, dict):
            index_map: Dict[int, str] = {}
            for token, positions in inverted.items():
                for pos in positions:
                    index_map[pos] = token
            return " ".join(index_map[idx] for idx in sorted(index_map))
        return payload.get("abstract", "") or payload.get("summary", "") or ""

    def _extract_authors(self, payload: Dict[str, Any]) -> List[str]:
        authors = []
        for authorship in payload.get("authorships", []):
            if not isinstance(authorship, dict):
                continue
            name = authorship.get("author", {}).get("display_name")
            if name:
                authors.append(name)
        if not authors and payload.get("authors"):
            authors.extend([str(author) for author in payload.get("authors", [])])
        return authors

    def _extract_keywords(self, payload: Dict[str, Any]) -> List[str]:
        keywords = []
        for concept in payload.get("concepts", []) or []:
            if isinstance(concept, dict) and concept.get("display_name"):
                keywords.append(concept["display_name"])
        if payload.get("keywords"):
            keywords.extend([str(keyword) for keyword in payload.get("keywords", [])])
        return keywords[:10]

    def _make_cache_key(self, papers: Sequence[SynthesizerPaper], max_words: int, style: str, focus: str) -> str:
        paper_ids = ",".join(sorted(paper.paper_id for paper in papers))
        return f"synth:{paper_ids}:{max_words}:{style}:{focus}".lower()

    async def _read_cache(self, key: str) -> Optional[Dict[str, Any]]:
        async with self._cache_lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            expires_at, value = entry
            if datetime.now(timezone.utc).timestamp() > expires_at:
                self._cache.pop(key, None)
                return None
            return dict(value)

    async def _write_cache(self, key: str, value: Dict[str, Any], ttl: int = 900) -> None:
        async with self._cache_lock:
            self._cache[key] = (datetime.now(timezone.utc).timestamp() + ttl, dict(value))


__all__ = ["EnhancedSynthesizer"]
