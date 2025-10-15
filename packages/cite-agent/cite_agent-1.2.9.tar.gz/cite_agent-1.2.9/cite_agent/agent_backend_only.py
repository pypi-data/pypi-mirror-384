"""
Backend-Only Agent (Distribution Version)
All LLM queries go through centralized backend API.
Local API keys are not supported.
"""

import os
import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class ChatRequest:
    question: str
    user_id: str = "default"
    conversation_id: str = "default"
    context: Dict[str, Any] = None

@dataclass
class ChatResponse:
    response: str
    citations: list = None
    tools_used: list = None
    model: str = "backend"
    timestamp: str = None
    tokens_used: int = 0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.citations is None:
            self.citations = []
        if self.tools_used is None:
            self.tools_used = []

class EnhancedNocturnalAgent:
    """
    Backend-only agent for distribution.
    Proxies all requests to centralized API.
    """

    def __init__(self):
        self.backend_url = (
            os.getenv("NOCTURNAL_CONTROL_PLANE_URL")
            or "https://cite-agent-api-720dfadd602c.herokuapp.com"
        )
        self.auth_token = None
        self.daily_token_usage = 0
        self._load_auth()

    def _load_auth(self):
        """Load authentication token from config"""
        # Try environment first
        self.auth_token = os.getenv("NOCTURNAL_AUTH_TOKEN")

        # Try config file
        if not self.auth_token:
            from pathlib import Path
            config_file = Path.home() / ".nocturnal_archive" / "config.env"
            if config_file.exists():
                with open(config_file) as f:
                    for line in f:
                        if line.startswith("NOCTURNAL_AUTH_TOKEN="):
                            self.auth_token = line.split("=", 1)[1].strip()
                            break

    async def initialize(self):
        """Initialize agent"""
        if not self.auth_token:
            return False
        return True

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Send chat request to backend API.

        Args:
            request: Chat request with question and context

        Returns:
            Chat response with answer and citations

        Raises:
            RuntimeError: If authentication fails or backend unavailable
        """
        if not self.auth_token:
            raise RuntimeError(
                "Not authenticated. Run 'cite-agent --setup' first."
            )

        try:
            response = requests.post(
                f"{self.backend_url}/api/query",
                headers={
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "query": request.question,
                    "context": request.context or {},
                    "user_id": request.user_id,
                    "conversation_id": request.conversation_id,
                },
                timeout=60
            )

            if response.status_code == 401:
                raise RuntimeError(
                    "Authentication expired. Run 'cite-agent --setup' to log in again."
                )

            if response.status_code == 429:
                raise RuntimeError(
                    "Daily quota exceeded (25,000 tokens). Resets tomorrow."
                )

            if response.status_code >= 400:
                error_detail = response.json().get("detail", response.text)
                raise RuntimeError(f"Backend error: {error_detail}")

            data = response.json()

            return ChatResponse(
                response=data.get("response", data.get("answer", "")),
                citations=data.get("citations", []),
                tools_used=data.get("tools_used", []),
                model=data.get("model", "backend"),
            )

        except requests.RequestException as e:
            raise RuntimeError(
                f"Backend connection failed: {e}. Check your internet connection."
            ) from e

    async def close(self):
        """Cleanup"""
        pass

    def get_health_status(self) -> Dict[str, Any]:
        """Get backend health status"""
        try:
            response = requests.get(
                f"{self.backend_url}/api/health/",
                timeout=5
            )
            return response.json()
        except:
            return {"status": "unavailable"}

    def check_quota(self) -> Dict[str, Any]:
        """Check remaining daily quota"""
        if not self.auth_token:
            raise RuntimeError("Not authenticated")

        response = requests.get(
            f"{self.backend_url}/api/auth/me",
            headers={"Authorization": f"Bearer {self.auth_token}"},
            timeout=10
        )

        if response.status_code == 401:
            raise RuntimeError("Authentication expired")

        response.raise_for_status()
        data = response.json()

        return {
            "tokens_used": data.get("tokens_used_today", 0),
            "tokens_remaining": data.get("tokens_remaining", 0),
            "daily_limit": 25000,
        }

    async def process_request(self, request: ChatRequest) -> ChatResponse:
        """Process request (alias for chat method for CLI compatibility)"""
        return await self.chat(request)

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for CLI display"""
        try:
            quota = self.check_quota()
            tokens_used = quota.get("tokens_used", 0)
            daily_limit = quota.get("daily_limit", 50000)
            usage_pct = (tokens_used / daily_limit * 100) if daily_limit > 0 else 0

            return {
                "daily_tokens_used": tokens_used,
                "daily_token_limit": daily_limit,
                "usage_percentage": usage_pct,
                "tokens_remaining": quota.get("tokens_remaining", 0)
            }
        except Exception:
            return {
                "daily_tokens_used": 0,
                "daily_token_limit": 50000,
                "usage_percentage": 0,
                "tokens_remaining": 50000
            }
