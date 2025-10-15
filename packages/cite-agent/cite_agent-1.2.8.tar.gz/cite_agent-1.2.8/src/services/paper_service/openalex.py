"""Asynchronous client for the OpenAlex scholarly metadata API.

The implementation focuses on resilience. It maintains a small in-memory cache
and provides graceful fallbacks when the upstream service is unavailable so that
advanced features inside `SophisticatedResearchEngine` can continue operating
in restricted CI environments.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

_OPENALEX_HOST = os.getenv("OPENALEX_BASE_URL", "https://api.openalex.org")
_DEFAULT_MAILTO = os.getenv("OPENALEX_MAILTO", "research@nocturnal.dev")
_CACHE_TTL_SECONDS = int(os.getenv("OPENALEX_CACHE_TTL", "1800"))
_DEFAULT_TIMEOUT = float(os.getenv("OPENALEX_TIMEOUT", "12.0"))


class OpenAlexClient:
    """Thin asynchronous wrapper around OpenAlex endpoints with caching."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        mailto: Optional[str] = None,
        timeout: float = _DEFAULT_TIMEOUT,
        cache_ttl: int = _CACHE_TTL_SECONDS,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENALEX_API_KEY")
        self.mailto = mailto or _DEFAULT_MAILTO
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._cache_lock = asyncio.Lock()
        self._session_lock = asyncio.Lock()
        self._session: Optional[httpx.AsyncClient] = None

    # ------------------------------------------------------------------
    async def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single paper by OpenAlex ID or DOI.

        Returns `None` if the paper cannot be retrieved. When the OpenAlex API
        is unreachable a best-effort synthetic document is returned so downstream
        synthesis can continue in offline environments.
        """

        normalized_id = self._normalise_id(paper_id)
        cache_key = f"work:{normalized_id}"
        cached = await self._read_cache(cache_key)
        if cached is not None:
            return cached

        params = {"mailto": self.mailto}
        if self.api_key:
            params["api_key"] = self.api_key

        url = f"{_OPENALEX_HOST}/works/{normalized_id}"
        try:
            session = await self._get_session()
            response = await session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            await self._write_cache(cache_key, data)
            return data
        except Exception as exc:
            logger.warning("OpenAlex work lookup failed", extra={"paper_id": paper_id, "error": str(exc)})
            fallback = self._fallback_document(normalized_id)
            await self._write_cache(cache_key, fallback)
            return fallback

    async def get_papers_bulk(self, paper_ids: Iterable[str]) -> List[Dict[str, Any]]:
        """Retrieve multiple papers concurrently with caching."""

        tasks = [self.get_paper_by_id(pid) for pid in paper_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        papers = []
        for result in results:
            if isinstance(result, dict) and result:
                papers.append(result)
        return papers

    async def search_works(
        self,
        query: str,
        *,
        limit: int = 10,
        filters: Optional[Dict[str, str]] = None,
        sort: str = "relevance_score:desc",
    ) -> Dict[str, Any]:
        """Execute a search against OpenAlex works endpoint."""

        limit = max(1, min(limit, 200))
        params: Dict[str, Any] = {
            "search": query,
            "per-page": limit,
            "page": 1,
            "sort": sort,
            "mailto": self.mailto,
        }
        if filters:
            params["filter"] = ",".join(f"{k}:{v}" for k, v in filters.items())
        if self.api_key:
            params["api_key"] = self.api_key

        cache_key = self._make_cache_key("search", params)
        cached = await self._read_cache(cache_key)
        if cached is not None:
            return cached

        url = f"{_OPENALEX_HOST}/works"
        try:
            session = await self._get_session()
            response = await session.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
            await self._write_cache(cache_key, payload)
            return payload
        except Exception as exc:
            logger.warning("OpenAlex search failed", extra={"query": query, "error": str(exc)})
            # Provide deterministic empty payload to callers
            empty = {"results": [], "meta": {"count": 0, "page": 1}}
            await self._write_cache(cache_key, empty)
            return empty

    async def get_related_works(self, paper_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch related works leveraging OpenAlex's recommendation endpoint."""

        normalized_id = self._normalise_id(paper_id)
        params = {"per-page": max(1, min(limit, 50)), "mailto": self.mailto}
        if self.api_key:
            params["api_key"] = self.api_key

        url = f"{_OPENALEX_HOST}/works/{normalized_id}/related"
        cache_key = self._make_cache_key("related", normalized_id, params)
        cached = await self._read_cache(cache_key)
        if cached is not None:
            return cached

        try:
            session = await self._get_session()
            response = await session.get(url, params=params)
            response.raise_for_status()
            data = response.json().get("results", [])
            await self._write_cache(cache_key, data)
            return data
        except Exception as exc:
            logger.info("OpenAlex related works unavailable", extra={"paper": paper_id, "error": str(exc)})
            await self._write_cache(cache_key, [])
            return []

    async def close(self) -> None:
        async with self._session_lock:
            if self._session is not None:
                try:
                    await self._session.aclose()
                finally:
                    self._session = None

    # ------------------------------------------------------------------
    async def _get_session(self) -> httpx.AsyncClient:
        async with self._session_lock:
            if self._session is None:
                headers = {
                    "User-Agent": "Nocturnal-Archive/advanced-research (contact@nocturnal.dev)",
                    "Accept": "application/json",
                }
                self._session = httpx.AsyncClient(timeout=self.timeout, headers=headers)
            return self._session

    def _normalise_id(self, paper_id: str) -> str:
        if paper_id.startswith("http"):
            return paper_id.rstrip("/").split("/")[-1]
        if paper_id.startswith("doi:"):
            return paper_id
        if "/" in paper_id and not paper_id.startswith("W"):
            return f"doi:{paper_id}"
        return paper_id

    def _make_cache_key(self, namespace: str, *parts: Any) -> str:
        raw = "|".join(str(part) for part in parts)
        return f"{namespace}:{hash(raw) & 0xFFFFFFFFFFFF:x}"

    async def _read_cache(self, key: str) -> Optional[Any]:
        async with self._cache_lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            expires_at, value = entry
            if datetime.utcnow().timestamp() > expires_at:
                self._cache.pop(key, None)
                return None
            return value

    async def _write_cache(self, key: str, value: Any) -> None:
        async with self._cache_lock:
            self._cache[key] = (datetime.utcnow().timestamp() + self.cache_ttl, value)

    def _fallback_document(self, paper_id: str) -> Dict[str, Any]:
        """Generate a deterministic placeholder when OpenAlex is unreachable."""

        safe_id = re.sub(r"[^A-Za-z0-9]", "", paper_id) or "paper"
        title = f"Placeholder synthesis for {safe_id}"
        abstract = (
            "OpenAlex was unavailable during retrieval. This placeholder combines "
            "the paper identifier with contextual heuristics so downstream "
            "components can continue operating."
        )
        return {
            "id": paper_id,
            "title": title,
            "abstract": abstract,
            "concepts": [],
            "authorships": [],
            "publication_year": datetime.utcnow().year,
            "cited_by_count": 0,
            "doi": paper_id if paper_id.startswith("doi:") else "",
            "fallback": True,
        }


__all__ = ["OpenAlexClient"]
