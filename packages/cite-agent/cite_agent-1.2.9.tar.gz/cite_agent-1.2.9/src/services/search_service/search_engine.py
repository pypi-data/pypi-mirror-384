"""High-level scholarly search orchestration service.

The engine aggregates OpenAlex, optional PubMed, and lightweight web results to
provide the advanced research surface required by the beta release. Emphasis is
placed on resilience: network failures or missing API keys degrade gracefully
instead of crashing the request path.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import httpx

from ..paper_service import OpenAlexClient
from ..performance_service.rust_performance import HighPerformanceService

logger = logging.getLogger(__name__)

_PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_DDG_PROXY = os.getenv("DDG_PROXY_URL", "https://ddg-webapp-aagd.vercel.app/search")


@dataclass(slots=True)
class SearchResult:
    """Canonical representation of a scholarly item."""

    id: str
    title: str
    abstract: str
    source: str
    authors: List[str]
    year: Optional[int]
    doi: str
    url: str
    relevance: float
    citations: int
    keywords: List[str]
    metadata: Dict[str, Any]


class SearchEngine:
    """Advanced scholarly search with optional enrichment."""

    def __init__(
        self,
        *,
        openalex_client: Optional[OpenAlexClient] = None,
        performance_service: Optional[HighPerformanceService] = None,
        redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379"),
        timeout: float = float(os.getenv("SEARCH_TIMEOUT", "12.0")),
    ) -> None:
        self.openalex = openalex_client or OpenAlexClient()
        self.performance = performance_service or HighPerformanceService()
        self.redis_url = redis_url
        self.timeout = timeout
        self._session = httpx.AsyncClient(timeout=timeout)
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    async def search_papers(
        self,
        query: str,
        *,
        limit: int = 10,
        sources: Optional[Sequence[str]] = None,
        include_metadata: bool = True,
        include_abstracts: bool = True,
        include_citations: bool = True,
    ) -> Dict[str, Any]:
        """Search across configured scholarly sources."""

        if not query or not query.strip():
            raise ValueError("Query must be a non-empty string")

        limit = max(1, min(limit, 100))
        sources = sources or ("openalex",)
        gathered: List[SearchResult] = []

        if "openalex" in sources:
            gathered.extend(await self._search_openalex(query, limit))

        if "pubmed" in sources:
            try:
                gathered.extend(await self._search_pubmed(query, limit))
            except Exception as exc:  # pragma: no cover - optional remote dependency
                logger.info("PubMed search failed", extra={"error": str(exc)})

        deduped = self._deduplicate_results(gathered)
        sorted_results = sorted(deduped, key=lambda item: item.relevance, reverse=True)[:limit]

        payload = {
            "query": query,
            "count": len(sorted_results),
            "sources_used": list(dict.fromkeys([res.source for res in sorted_results])),
            "papers": [self._result_to_payload(res, include_metadata, include_abstracts, include_citations) for res in sorted_results],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        return payload

    async def web_search(self, query: str, *, num_results: int = 5) -> List[Dict[str, Any]]:
        """Perform a lightweight DuckDuckGo-backed web search."""

        params = {"q": query, "max_results": max(1, min(num_results, 10))}
        try:
            response = await self._session.get(_DDG_PROXY, params=params)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", []) if isinstance(data, dict) else []
            formatted = [
                {
                    "title": item.get("title", ""),
                    "url": item.get("href") or item.get("link") or "",
                    "snippet": item.get("body") or item.get("snippet") or "",
                    "source": item.get("source", "duckduckgo"),
                }
                for item in results[:num_results]
            ]
            return formatted
        except Exception as exc:  # pragma: no cover - network optional
            logger.info("Web search fallback", extra={"error": str(exc)})
            return []

    async def fetch_paper_bundle(self, paper_ids: Iterable[str]) -> List[Dict[str, Any]]:
        """Convenience helper for fetching OpenAlex metadata for multiple IDs."""

        papers = await self.openalex.get_papers_bulk(paper_ids)
        formatted: List[Dict[str, Any]] = []
        for paper in papers:
            formatted.append(self._format_openalex_work(paper))
        return formatted

    async def close(self) -> None:
        await self.openalex.close()
        try:
            await self._session.aclose()
        except Exception:
            pass

    # ------------------------------------------------------------------
    async def _search_openalex(self, query: str, limit: int) -> List[SearchResult]:
        payload = await self.openalex.search_works(
            query,
            limit=limit,
            filters={"type": "journal-article"},
        )
        results = payload.get("results", []) if isinstance(payload, dict) else []
        formatted = [self._format_openalex_work(item) for item in results]

        if formatted:
            try:
                combined = "\n".join(res.abstract for res in formatted if res.abstract)
                if combined:
                    keywords = await self.performance.extract_keywords(combined, max_keywords=10)
                    for res in formatted:
                        res.metadata.setdefault("query_keywords", keywords)
            except Exception:
                # Keyword enrichment is best-effort
                pass

        return formatted

    async def _search_pubmed(self, query: str, limit: int) -> List[SearchResult]:
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max(1, min(limit, 50)),
            "retmode": "json",
            "sort": "relevance",
        }
        search_url = f"{_PUBMED_BASE}/esearch.fcgi"
        response = await self._session.get(search_url, params=params)
        response.raise_for_status()
        id_list = response.json().get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return []

        summary_params = {
            "db": "pubmed",
            "id": ",".join(id_list[:limit]),
            "retmode": "json",
        }
        summary_url = f"{_PUBMED_BASE}/esummary.fcgi"
        summary_resp = await self._session.get(summary_url, params=summary_params)
        summary_resp.raise_for_status()
        summaries = summary_resp.json().get("result", {})

        results: List[SearchResult] = []
        for pmid in id_list[:limit]:
            raw = summaries.get(pmid)
            if not isinstance(raw, dict):
                continue
            title = raw.get("title", "")
            abstract = raw.get("elocationid", "") or raw.get("source", "")
            authors = [author.get("name", "") for author in raw.get("authors", []) if isinstance(author, dict)]
            results.append(
                SearchResult(
                    id=f"PMID:{pmid}",
                    title=title,
                    abstract=abstract,
                    source="pubmed",
                    authors=[a for a in authors if a],
                    year=self._safe_int(raw.get("pubdate", "")[:4]),
                    doi=raw.get("elocationid", ""),
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    relevance=0.6,
                    citations=raw.get("pmc", 0) or 0,
                    keywords=[],
                    metadata={"pmid": pmid},
                )
            )
        return results

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        seen: Dict[str, SearchResult] = {}
        for result in results:
            key = result.doi.lower() if result.doi else result.title.lower()
            if key in seen:
                existing = seen[key]
                if result.relevance > existing.relevance:
                    seen[key] = result
            else:
                seen[key] = result
        return list(seen.values())

    def _format_openalex_work(self, work: Dict[str, Any]) -> SearchResult:
        title = work.get("title", "")
        abstract = self._extract_openalex_abstract(work)
        authors = [
            auth.get("author", {}).get("display_name", "")
            for auth in work.get("authorships", [])
            if isinstance(auth, dict)
        ]
        doi = work.get("doi", "") or ""
        url = work.get("id", "")
        concepts = [concept.get("display_name", "") for concept in work.get("concepts", []) if isinstance(concept, dict)]
        citations = work.get("cited_by_count", 0) or 0
        relevance = work.get("relevance_score", 0.0) or 0.5 + min(0.4, citations / 1000)

        keywords = concepts[:5] or self._quick_keywords(abstract, limit=5)

        metadata = {
            "openalex_id": url,
            "open_access": work.get("open_access", {}).get("is_oa", False),
            "primary_location": work.get("primary_location"),
        }

        return SearchResult(
            id=url.split("/")[-1] if url else doi or title,
            title=title,
            abstract=abstract,
            source="openalex",
            authors=[a for a in authors if a],
            year=work.get("publication_year"),
            doi=doi.replace("https://doi.org/", ""),
            url=url or f"https://openalex.org/{title[:50].replace(' ', '_')}",
            relevance=float(relevance),
            citations=citations,
            keywords=keywords,
            metadata=metadata,
        )

    def _result_to_payload(
        self,
        result: SearchResult,
        include_metadata: bool,
        include_abstracts: bool,
        include_citations: bool,
    ) -> Dict[str, Any]:
        payload = {
            "id": result.id,
            "title": result.title,
            "source": result.source,
            "authors": result.authors,
            "year": result.year,
            "doi": result.doi,
            "url": result.url,
            "keywords": result.keywords,
            "relevance": result.relevance,
        }
        if include_abstracts:
            payload["abstract"] = result.abstract
        if include_citations:
            payload["citations_count"] = result.citations
        if include_metadata:
            payload["metadata"] = result.metadata
        return payload

    def _extract_openalex_abstract(self, work: Dict[str, Any]) -> str:
        inverted = work.get("abstract_inverted_index")
        if isinstance(inverted, dict) and inverted:
            # Convert inverted index back to human-readable abstract
            index_map: Dict[int, str] = {}
            for token, positions in inverted.items():
                for position in positions:
                    index_map[position] = token
            abstract_tokens = [token for _, token in sorted(index_map.items())]
            return " ".join(abstract_tokens)
        return work.get("abstract", "") or ""

    def _safe_int(self, value: Any) -> Optional[int]:
        try:
            return int(value)
        except Exception:
            return None

    def _quick_keywords(self, text: str, limit: int = 5) -> List[str]:
        import re
        from collections import Counter

        if not text:
            return []

        words = re.findall(r"[a-zA-Z]{3,}", text.lower())
        stop_words = {
            "the",
            "and",
            "for",
            "with",
            "from",
            "that",
            "have",
            "this",
            "were",
            "also",
            "into",
            "which",
            "their",
            "between",
            "within",
        }
        filtered = [word for word in words if word not in stop_words]
        most_common = Counter(filtered).most_common(limit)
        return [word for word, _ in most_common]


__all__ = ["SearchEngine"]
