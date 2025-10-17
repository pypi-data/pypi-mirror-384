"""Runtime-focused tests for the enhanced AI agent."""

import asyncio
import time
from typing import List

import pytest

from nocturnal_archive.enhanced_ai_agent import (
    ChatRequest,
    ChatResponse,
    EnhancedNocturnalAgent,
)
from nocturnal_archive.setup_config import DEFAULT_QUERY_LIMIT


def test_chat_dataclasses_use_isolated_defaults():
    request_a = ChatRequest(question="hello")
    request_a.context["foo"] = "bar"

    request_b = ChatRequest(question="world")

    assert request_b.context == {}

    response_a = ChatResponse(response="one")
    response_b = ChatResponse(response="two")

    response_a.tools_used.append("alpha")
    response_a.api_results["metric"] = 42

    assert response_b.tools_used == []
    assert response_b.api_results == {}
    assert isinstance(response_a.timestamp, str) and response_a.timestamp


@pytest.mark.asyncio
async def test_get_financial_metrics_runs_concurrently():
    agent = EnhancedNocturnalAgent()

    call_order = []

    async def fake_call(endpoint: str, params=None):
        call_order.append(endpoint)
        await asyncio.sleep(0.05)
        return {"endpoint": endpoint}

    agent._call_finsight_api = fake_call  # type: ignore[assignment]

    started = time.perf_counter()
    result = await agent.get_financial_metrics("TEST", ["metricA", "metricB", "metricC"])
    elapsed = time.perf_counter() - started

    assert len(result) == 3
    assert set(result.keys()) == {"metricA", "metricB", "metricC"}
    assert len(call_order) == 3
    assert elapsed < 0.14

    await agent.close()


@pytest.mark.asyncio
async def test_async_context_manager_closes_resources():
    class _DummySession:
        def __init__(self):
            self.closed = False

        async def close(self):
            self.closed = True

    class _DummyShell:
        def __init__(self):
            self.terminated = False

        def terminate(self):
            self.terminated = True

        def poll(self):
            return None

    class _DummyAgent(EnhancedNocturnalAgent):
        async def initialize(self, force_reload: bool = False):  # type: ignore[override]
            lock = self._get_init_lock()
            async with lock:
                self.session = _DummySession()
                self.shell_session = _DummyShell()
                self._initialized = True
                return True

    agent = _DummyAgent()
    session_ref = None
    shell_ref = None

    async with agent as active_agent:
        assert active_agent._initialized
        assert isinstance(active_agent.session, _DummySession)
        assert isinstance(active_agent.shell_session, _DummyShell)
        session_ref = active_agent.session
        shell_ref = active_agent.shell_session

    assert agent.session is None
    assert agent.shell_session is None
    assert not agent._initialized
    assert session_ref is not None and session_ref.closed
    assert shell_ref is not None and shell_ref.terminated


def test_command_summary_falls_back_without_llm(monkeypatch):
    agent = EnhancedNocturnalAgent()
    # Prevent real model calls
    monkeypatch.setattr(agent, "_ensure_client_ready", lambda: False)

    base = "Base response"
    updated, tokens = agent._summarize_command_output(
        ChatRequest(question="run `ls`"),
        "ls",
        "alpha\nbeta",
        base
    )

    assert "```shell" in updated
    assert "$ ls" in updated
    assert "alpha" in updated
    assert tokens == 0


def test_shell_blocked_response_includes_policy_message(monkeypatch):
    agent = EnhancedNocturnalAgent()
    request = ChatRequest(question="run: rm -rf /")

    response = agent._respond_with_shell_command(request, "rm -rf /")

    assert response.tools_used == ["shell_blocked"]
    assert "violates the safety policy" in response.response
    assert response.execution_results["success"] is False
    assert "Command blocked" in response.execution_results["output"]


def test_shell_safety_rejects_dangerous_rm(monkeypatch, tmp_path):
    agent = EnhancedNocturnalAgent()
    monkeypatch.chdir(tmp_path)
    safe_file = tmp_path / "safe.txt"
    safe_file.write_text("ok")

    assert agent._is_safe_shell_command("rm safe.txt")
    assert not agent._is_safe_shell_command("rm -rf safe.txt")
    assert not agent._is_safe_shell_command("rm ../oops.txt")
    assert not agent._is_safe_shell_command("rm /etc/passwd")
    assert not agent._is_safe_shell_command("rm danger*.txt")


def test_workspace_listing_formatter_handles_metadata():
    agent = EnhancedNocturnalAgent()
    agent._recent_sources = [
        {"service": "Files", "endpoint": "GET /", "success": True}
    ]
    listing = {
        "base": "/repo",
        "items": [
            {"name": f"file{i}.txt", "type": "file"} for i in range(15)
        ],
        "note": "Showing limited snapshot",
        "truncated": True,
        "error": "Upstream timeout"
    }

    message = agent._format_workspace_listing_response(listing)

    assert "Workspace root: /repo" in message
    assert message.count("file") >= 12
    assert "… and 3 more" in message
    assert "Showing limited snapshot" in message
    assert "Upstream timeout" in message
    assert "Data sources:" in message


@pytest.mark.asyncio
async def test_process_request_finance_handles_multi_ticker(monkeypatch):
    agent = EnhancedNocturnalAgent()

    async def fake_get_financial_metrics(ticker: str, metrics):
        fake_get_financial_metrics.calls.append((ticker, tuple(metrics)))
        return {
            metric: {"value": 123456789, "period": "2024-Q2", "citations": []}
            for metric in metrics
        }

    fake_get_financial_metrics.calls = []  # type: ignore[attr-defined]

    async def fake_search(query: str, limit: int = 10):
        return {"results": []}

    monkeypatch.setattr(agent, "get_financial_metrics", fake_get_financial_metrics)
    monkeypatch.setattr(agent, "search_academic_papers", fake_search)
    monkeypatch.setattr(agent, "_ensure_client_ready", lambda: False)

    request = ChatRequest(
        question="Compare revenue and net income for Apple and Microsoft this quarter"
    )

    response = await agent.process_request(request)

    assert fake_get_financial_metrics.calls == [
        ("AAPL", ("revenue", "netIncome")),
        ("MSFT", ("revenue", "netIncome")),
    ]

    payload = response.api_results.get("financial")
    assert payload is not None
    assert {"AAPL", "MSFT"} <= set(payload.keys())
    assert "Finance API snapshot" in response.response or "AAPL" in response.response

    await agent.close()


@pytest.mark.asyncio
async def test_search_academic_papers_falls_back_to_single_source(monkeypatch):
    agent = EnhancedNocturnalAgent()

    call_order: List[List[str]] = []

    async def fake_archive_call(endpoint: str, data):
        call_order.append(list(data["sources"]))
        if data["sources"] == ["semantic_scholar", "openalex"]:
            return {"results": []}
        if data["sources"] == ["semantic_scholar"]:
            return {"results": []}
        if data["sources"] == ["openalex"]:
            return {"results": [{"id": "openalex:123", "title": "Sample"}]}
        return {"results": []}

    monkeypatch.setattr(agent, "_call_archive_api", fake_archive_call)

    result = await agent.search_academic_papers("graph neural networks", limit=3)

    assert result["results"] and result["results"][0]["id"] == "openalex:123"
    assert call_order == [["semantic_scholar", "openalex"], ["semantic_scholar"], ["openalex"]]
    assert "notes" not in result


@pytest.mark.asyncio
async def test_search_academic_papers_reports_provider_errors(monkeypatch):
    agent = EnhancedNocturnalAgent()

    async def fake_archive_call(endpoint: str, data):
        if data["sources"] == ["openalex"]:
            return {"error": "Archive API rate limited. Please try again later."}
        return {"results": []}

    monkeypatch.setattr(agent, "_call_archive_api", fake_archive_call)

    result = await agent.search_academic_papers("obscure topic", limit=2)

    assert result["results"] == []
    assert "notes" in result and "retry" in result["notes"].lower()
    assert result.get("provider_errors")


@pytest.mark.asyncio
async def test_probe_health_endpoint_falls_back_to_root(monkeypatch):
    agent = EnhancedNocturnalAgent()

    class _MockResponse:
        def __init__(self, status: int, body: str = ""):
            self.status = status
            self._body = body
            self.content_type = "text/plain"

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def text(self):
            return self._body

    class _MockSession:
        def __init__(self):
            self.calls: List[str] = []

        def get(self, url, timeout=5):
            self.calls.append(url)
            if url.endswith("/readyz"):
                return _MockResponse(404)
            if url.endswith("/health") or url.endswith("/api/health") or url.endswith("/livez"):
                return _MockResponse(404)
            if url == "http://example.com":
                return _MockResponse(200)
            return _MockResponse(500)

    agent.session = _MockSession()

    ok, detail = await agent._probe_health_endpoint("http://example.com")

    assert ok
    assert "fallback probe" in detail.lower()


@pytest.mark.asyncio
async def test_daily_query_limit_enforced(monkeypatch):
    agent = EnhancedNocturnalAgent()
    agent.daily_query_limit = 2
    agent.per_user_query_limit = 2

    monkeypatch.setattr(agent, "_ensure_client_ready", lambda: False)

    await agent.process_request(ChatRequest(question="first", user_id="tester"))
    await agent.process_request(ChatRequest(question="second", user_id="tester"))
    third = await agent.process_request(ChatRequest(question="third", user_id="tester"))

    assert "Daily query limit" in third.response
    assert third.tools_used == ["rate_limit"]
    assert agent.daily_query_count == 2

    await agent.close()


def test_query_limit_signature_tampering(monkeypatch):
    monkeypatch.setenv("NOCTURNAL_QUERY_LIMIT", "999")
    monkeypatch.setenv("NOCTURNAL_QUERY_LIMIT_SIG", "bogus")

    agent = EnhancedNocturnalAgent()

    assert agent.daily_query_limit == DEFAULT_QUERY_LIMIT

