"""Tests for Archive integration in the enhanced agent."""

import pytest

from nocturnal_archive.enhanced_ai_agent import EnhancedNocturnalAgent


class _MockResponse:
    def __init__(self, status: int, payload=None):
        self.status = status
        self._payload = payload or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        return self._payload


class _MockSession:
    def __init__(self, response: _MockResponse):
        self.response = response
        self.post_calls = []

    def post(self, url, json=None, headers=None, **kwargs):
        self.post_calls.append({
            "url": url,
            "json": json,
            "headers": headers,
            "extra": kwargs,
        })
        return self.response


@pytest.mark.asyncio
async def test_call_archive_api_success():
    agent = EnhancedNocturnalAgent()

    agent._default_headers = {"X-API-Key": "test-key"}

    mock_session = _MockSession(_MockResponse(200, {"result": "ok"}))
    agent.session = mock_session

    payload = {"query": "graph learning", "limit": 5}
    result = await agent._call_archive_api("search", payload)

    assert result == {"result": "ok"}
    assert mock_session.post_calls == [
        {
            "url": "http://127.0.0.1:8000/api/search",
            "json": payload,
            "headers": {"X-API-Key": "test-key"},
            "extra": {"timeout": 30},
        }
    ]


@pytest.mark.asyncio
async def test_call_archive_api_handles_error():
    agent = EnhancedNocturnalAgent()
    agent._default_headers = {}

    mock_session = _MockSession(_MockResponse(500))
    agent.session = mock_session

    result = await agent._call_archive_api("search", {"query": "x"})

    assert "error" in result
    assert "Archive API error" in result["error"]