"""Unified large language model management utilities.

This module exposes :class:`LLMManager`, a production-ready orchestration layer that
coordinates multiple LLM providers (Groq, OpenAI, Anthropic) while providing
advanced routing, caching, observability, and graceful fallbacks when GPU-backed
models are unavailable. The implementation is intentionally defensive: it never
raises provider-specific exceptions to callers and instead downgrades to a
high-quality heuristic summariser so the broader research pipeline can continue
functioning in constrained environments (including unit tests).
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:  # Optional dependency – only loaded when available
    from groq import Groq  # type: ignore
except Exception:  # pragma: no cover - optional provider
    Groq = None  # type: ignore

try:  # OpenAI >=1.x
    from openai import AsyncOpenAI  # type: ignore
except Exception:  # pragma: no cover - optional provider
    AsyncOpenAI = None  # type: ignore

try:  # Anthropic python client
    from anthropic import AsyncAnthropic  # type: ignore
except Exception:  # pragma: no cover - optional provider
    AsyncAnthropic = None  # type: ignore

# Default models for each provider. These can be overridden via environment
# variables or method arguments but serve as sensible, production-tested
# defaults that balance latency and quality.
DEFAULT_PROVIDER_MODELS: Dict[str, str] = {
    "groq": os.getenv("NA_GROQ_MODEL", "llama-3.1-70b-versatile"),
    "openai": os.getenv("NA_OPENAI_MODEL", "gpt-4.1-mini"),
    "anthropic": os.getenv("NA_ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
}

# Maximum tokens for synthesis generations. Exposed for easy tuning via env.
DEFAULT_MAX_TOKENS = int(os.getenv("NA_MAX_SYNTHESIS_TOKENS", "2048"))
DEFAULT_TEMPERATURE = float(os.getenv("NA_SYNTHESIS_TEMPERATURE", "0.2"))


@dataclass(slots=True)
class ProviderSelection:
    """Information about the provider/model combination chosen for a request."""

    provider: str
    model: str
    reason: str


class LLMManager:
    """Unified interface across Groq, OpenAI, Anthropic, and heuristic fallbacks.

    The manager exposes a coroutine-based API that can be safely used inside
    FastAPI endpoints or background workers. Each call records latency and
    usage metadata which is returned to callers so that higher levels can make
    routing decisions or surface telemetry.
    """

    _PROVIDER_ENV_KEYS: Dict[str, Tuple[str, ...]] = {
        "groq": ("GROQ_API_KEY", "NA_GROQ_API_KEY"),
        "openai": ("OPENAI_API_KEY", "NA_OPENAI_API_KEY"),
        "anthropic": ("ANTHROPIC_API_KEY", "NA_ANTHROPIC_API_KEY"),
    }

    def __init__(
        self,
        *,
        redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379"),
        default_provider: Optional[str] = None,
        default_model: Optional[str] = None,
        cache_ttl: int = 900,
    ) -> None:
        self.redis_url = redis_url
        self._default_provider = (default_provider or os.getenv("NA_LLM_PROVIDER") or "groq").lower()
        self._default_model = default_model or DEFAULT_PROVIDER_MODELS.get(self._default_provider, "")
        self._cache_ttl = cache_ttl
        self._cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._cache_lock = asyncio.Lock()
        self._client_lock = asyncio.Lock()
        self._clients: Dict[str, Any] = {}
        self._last_health_check: Dict[str, Dict[str, Any]] = {}

        # Lazily-created loop for running sync provider clients (Groq) in a
        # thread pool. We reuse the default loop to avoid spawning threads per
        # request.
        self._loop = asyncio.get_event_loop()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def generate_synthesis(
        self,
        documents: Iterable[Dict[str, Any]],
        prompt: str,
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate a synthesis across documents using the best available LLM.

        Returns a dictionary containing the summary, metadata about the route
        taken, usage information, and latency. The structure is intentionally
        aligned with what the API layer expects when presenting advanced
        synthesis results.
        """

        documents = list(documents or [])
        serialized_context = self._serialize_documents(documents)
        cache_key = self._make_cache_key("synthesis", serialized_context, prompt, provider, model)

        cached = await self._read_cache(cache_key)
        if cached is not None:
            cached_copy = dict(cached)
            cached_copy["cached"] = True
            return cached_copy

        selection = await self._select_provider(provider, model)
        start = time.perf_counter()

        try:
            summary, usage = await self._invoke_provider(
                selection,
                self._build_messages(serialized_context, prompt),
                temperature or DEFAULT_TEMPERATURE,
                max_tokens or DEFAULT_MAX_TOKENS,
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.warning(
                "LLM provider invocation failed; falling back to heuristic",
                extra={"provider": selection.provider, "model": selection.model, "error": str(exc)},
            )
            summary = self._heuristic_summary(serialized_context, prompt)
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "fallback": True}
            selection = ProviderSelection(provider="heuristic", model="text-rank", reason=str(exc))

        latency = time.perf_counter() - start
        result = {
            "summary": summary.strip(),
            "provider": selection.provider,
            "model": selection.model,
            "reason": selection.reason,
            "usage": usage,
            "latency": latency,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }

        await self._write_cache(cache_key, result)
        return result

    async def generate_text(
        self,
        prompt: str,
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate free-form text using the same routing heuristics."""

        result = await self.generate_synthesis(
            documents=[],
            prompt=prompt,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return result.get("summary", "")

    async def health_check(self) -> Dict[str, Any]:
        """Return current provider availability and cached connectivity info."""

        statuses = {}
        for provider in ("groq", "openai", "anthropic"):
            statuses[provider] = {
                "configured": self._get_api_key(provider) is not None,
                "client_initialized": provider in self._clients,
                "last_error": None,
            }

        self._last_health_check = statuses
        return statuses

    async def close(self) -> None:
        """Close any underlying async clients (OpenAI/Anthropic)."""

        async with self._client_lock:
            openai_client = self._clients.get("openai")
            if openai_client and hasattr(openai_client, "close"):
                try:
                    await openai_client.close()  # type: ignore[attr-defined]
                except Exception:
                    pass
            anthropic_client = self._clients.get("anthropic")
            if anthropic_client and hasattr(anthropic_client, "close"):
                try:
                    await anthropic_client.close()  # type: ignore[attr-defined]
                except Exception:
                    pass
            # Groq client is synchronous – nothing to close
            self._clients.clear()

    # ------------------------------------------------------------------
    # Provider selection & invocation
    # ------------------------------------------------------------------
    async def _select_provider(
        self,
        provider: Optional[str],
        model: Optional[str],
    ) -> ProviderSelection:
        """Select the best available provider/model pair for the request."""

        candidate_order = []
        if provider:
            candidate_order.append(provider.lower())
        if self._default_provider not in candidate_order:
            candidate_order.append(self._default_provider)
        candidate_order.extend(["groq", "openai", "anthropic"])

        seen = set()
        for candidate in candidate_order:
            if candidate in seen:
                continue
            seen.add(candidate)
            api_key = self._get_api_key(candidate)
            if not api_key:
                continue
            selected_model = model or self._default_model or DEFAULT_PROVIDER_MODELS.get(candidate)
            if not selected_model:
                continue
            if await self._ensure_client(candidate, api_key):
                reason = "requested" if candidate == provider else "fallback"
                return ProviderSelection(provider=candidate, model=selected_model, reason=reason)

        logger.warning("No LLM providers configured; using heuristic summariser")
        return ProviderSelection(provider="heuristic", model="text-rank", reason="no-provider-configured")

    async def _ensure_client(self, provider: str, api_key: str) -> bool:
        """Instantiate and cache provider clients lazily."""

        if provider == "heuristic":
            return True

        async with self._client_lock:
            if provider in self._clients:
                return True

            try:
                if provider == "groq":
                    if Groq is None:  # pragma: no cover - optional provider
                        raise RuntimeError("groq package not installed")
                    self._clients[provider] = Groq(api_key=api_key)
                    return True

                if provider == "openai":
                    if AsyncOpenAI is None:  # pragma: no cover - optional provider
                        raise RuntimeError("openai package not installed")
                    self._clients[provider] = AsyncOpenAI(api_key=api_key)
                    return True

                if provider == "anthropic":
                    if AsyncAnthropic is None:  # pragma: no cover - optional provider
                        raise RuntimeError("anthropic package not installed")
                    self._clients[provider] = AsyncAnthropic(api_key=api_key)
                    return True

                raise ValueError(f"Unknown provider: {provider}")
            except Exception as exc:  # pragma: no cover - provider bootstrap is optional
                logger.warning("Failed to initialise LLM provider", extra={"provider": provider, "error": str(exc)})
                self._clients.pop(provider, None)
                return False

    async def _invoke_provider(
        self,
        selection: ProviderSelection,
        messages: List[Dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> Tuple[str, Dict[str, Any]]:
        """Invoke the selected provider and normalise the response."""

        if selection.provider == "heuristic":
            return self._heuristic_summary(messages[-1]["content"], ""), {  # type: ignore[index]
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "fallback": True,
            }

        client = self._clients.get(selection.provider)
        if client is None:
            raise RuntimeError(f"Provider {selection.provider} not initialised")

        if selection.provider == "groq":
            return await self._invoke_groq(client, selection.model, messages, temperature, max_tokens)
        if selection.provider == "openai":
            return await self._invoke_openai(client, selection.model, messages, temperature, max_tokens)
        if selection.provider == "anthropic":
            return await self._invoke_anthropic(client, selection.model, messages, temperature, max_tokens)

        raise ValueError(f"Unsupported provider: {selection.provider}")

    async def _invoke_groq(self, client: Any, model: str, messages: List[Dict[str, Any]], temperature: float, max_tokens: int) -> Tuple[str, Dict[str, Any]]:
        """Invoke Groq's chat completion API (synchronous client)."""

        def _call() -> Tuple[str, Dict[str, Any]]:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            message = response.choices[0].message.content if response.choices else ""
            usage = getattr(response, "usage", None)
            normalised_usage = {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                "completion_tokens": getattr(usage, "completion_tokens", 0),
                "total_tokens": getattr(usage, "total_tokens", 0),
            }
            return message or "", normalised_usage

        return await asyncio.to_thread(_call)

    async def _invoke_openai(self, client: Any, model: str, messages: List[Dict[str, Any]], temperature: float, max_tokens: int) -> Tuple[str, Dict[str, Any]]:
        response = await client.chat.completions.create(  # type: ignore[attr-defined]
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0] if response.choices else None
        message = choice.message.content if choice and choice.message else ""
        usage = getattr(response, "usage", None) or {}
        normalised_usage = {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0),
            "completion_tokens": getattr(usage, "completion_tokens", 0),
            "total_tokens": getattr(usage, "total_tokens", 0),
        }
        return message or "", normalised_usage

    async def _invoke_anthropic(self, client: Any, model: str, messages: List[Dict[str, Any]], temperature: float, max_tokens: int) -> Tuple[str, Dict[str, Any]]:
        system_prompt = """You are an advanced research assistant that creates meticulous literature syntheses."""
        anthropic_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "system":
                system_prompt = content
                continue
            anthropic_messages.append({"role": "user" if role == "user" else "assistant", "content": content})

        response = await client.messages.create(  # type: ignore[attr-defined]
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=anthropic_messages,
        )
        text = ""
        if response.content:
            content_block = response.content[0]
            text = getattr(content_block, "text", "") or getattr(content_block, "input_text", "")
        usage = getattr(response, "usage", None) or {}
        normalised_usage = {
            "prompt_tokens": getattr(usage, "input_tokens", 0),
            "completion_tokens": getattr(usage, "output_tokens", 0),
            "total_tokens": getattr(usage, "input_tokens", 0) + getattr(usage, "output_tokens", 0),
        }
        return text, normalised_usage

    # ------------------------------------------------------------------
    # Caching helpers
    # ------------------------------------------------------------------
    def _make_cache_key(self, namespace: str, *parts: Any) -> str:
        digest = hashlib.sha256()
        digest.update(namespace.encode("utf-8"))
        for part in parts:
            data = part if isinstance(part, str) else repr(part)
            digest.update(b"|")
            digest.update(data.encode("utf-8", errors="ignore"))
        return digest.hexdigest()

    async def _read_cache(self, key: str) -> Optional[Dict[str, Any]]:
        async with self._cache_lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            expires_at, value = entry
            if time.time() > expires_at:
                self._cache.pop(key, None)
                return None
            return dict(value)

    async def _write_cache(self, key: str, value: Dict[str, Any]) -> None:
        async with self._cache_lock:
            self._cache[key] = (time.time() + self._cache_ttl, dict(value))

    # ------------------------------------------------------------------
    # Prompt + context utilities
    # ------------------------------------------------------------------
    def _serialize_documents(self, documents: List[Dict[str, Any]]) -> str:
        if not documents:
            return ""
        blocks = []
        for idx, document in enumerate(documents, start=1):
            title = document.get("title") or document.get("name") or f"Document {idx}"
            section_lines = [f"### {title}".strip()]
            if document.get("authors"):
                authors = ", ".join(
                    a.get("name", "") if isinstance(a, dict) else str(a)
                    for a in document.get("authors", [])
                )
                if authors:
                    section_lines.append(f"*Authors:* {authors}")
            if document.get("year"):
                section_lines.append(f"*Year:* {document['year']}")
            abstract = document.get("abstract") or document.get("content") or document.get("text")
            if abstract:
                section_lines.append("\n" + str(abstract).strip())
            if document.get("highlights"):
                section_lines.append("\nKey Findings:\n- " + "\n- ".join(map(str, document["highlights"])))
            blocks.append("\n".join(section_lines).strip())
        return "\n\n".join(blocks)

    def _build_messages(self, serialized_context: str, prompt: str) -> List[Dict[str, Any]]:
        system_prompt = (
            "You are Nocturnal Archive's synthesis orchestrator. "
            "Produce rigorous, citation-ready summaries that emphasise methodology, "
            "effect sizes, limitations, and consensus versus disagreement."
        )
        user_prompt = (
            prompt.format(context=serialized_context)
            if "{context}" in prompt
            else f"{prompt.strip()}\n\nContext:\n{serialized_context.strip()}"
        ).strip()
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _heuristic_summary(self, serialized_context: str, prompt: str) -> str:
        """Fallback summariser using a TextRank-style scoring over sentences."""

        import re
        from collections import Counter, defaultdict

        text = serialized_context or prompt
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        if not sentences:
            return text.strip()

        words = re.findall(r"[a-zA-Z0-9']+", text.lower())
        frequencies = Counter(words)
        max_freq = max(frequencies.values() or [1])
        for key in frequencies:
            frequencies[key] /= max_freq

        sentence_scores: Dict[str, float] = defaultdict(float)
        for sentence in sentences:
            for word in re.findall(r"[a-zA-Z0-9']+", sentence.lower()):
                sentence_scores[sentence] += frequencies.get(word, 0.0)

        top_sentences = sorted(sentence_scores.items(), key=lambda kv: kv[1], reverse=True)[: min(5, len(sentences))]
        ordered = sorted(top_sentences, key=lambda kv: sentences.index(kv[0]))
        return " ".join(sentence for sentence, _ in ordered).strip()

    # ------------------------------------------------------------------
    # Misc utilities
    # ------------------------------------------------------------------
    def _get_api_key(self, provider: str) -> Optional[str]:
        for env_key in self._PROVIDER_ENV_KEYS.get(provider, ()):  # type: ignore[arg-type]
            value = os.getenv(env_key)
            if value:
                return value
        return None


__all__ = ["LLMManager"]
