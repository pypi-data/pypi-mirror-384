"""
Backend-only client for distribution.
All queries are proxied through the centralized backend.
Local LLM calls are not supported.
"""

import os
import requests
from typing import Dict, Any, Optional

class BackendOnlyClient:
    """
    Minimal client that only talks to backend API.
    Used in distribution to prevent local API key usage.
    """

    def __init__(self):
        self.backend_url = (
            os.getenv("NOCTURNAL_CONTROL_PLANE_URL")
            or "https://cite-agent-api-720dfadd602c.herokuapp.com"
        )
        self.auth_token = os.getenv("NOCTURNAL_AUTH_TOKEN")

    def query(self, message: str, style: str = "academic") -> Dict[str, Any]:
        """
        Send query to backend API.

        Args:
            message: User query
            style: Response style

        Returns:
            Backend response with citations

        Raises:
            RuntimeError: If not authenticated or backend unavailable
        """
        if not self.auth_token:
            raise RuntimeError(
                "Not authenticated. Run 'cite-agent --setup' first."
            )

        try:
            response = requests.post(
                f"{self.backend_url}/api/query",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                json={"query": message, "style": style},
                timeout=30
            )

            if response.status_code == 401:
                raise RuntimeError(
                    "Authentication failed. Your token may have expired. "
                    "Run 'cite-agent --setup' to log in again."
                )

            if response.status_code == 429:
                raise RuntimeError(
                    "Daily quota exceeded (25,000 tokens/day). "
                    "Your quota will reset tomorrow."
                )

            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            raise RuntimeError(
                f"Backend unavailable: {e}. "
                f"Please check your internet connection or try again later."
            ) from e

    def check_quota(self) -> Dict[str, Any]:
        """Check remaining daily quota"""
        if not self.auth_token:
            raise RuntimeError("Not authenticated")

        response = requests.get(
            f"{self.backend_url}/api/auth/me",
            headers={"Authorization": f"Bearer {self.auth_token}"},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
