"""Account provisioning utilities for the Nocturnal Archive CLI."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional


class AccountProvisioningError(RuntimeError):
    """Raised when account provisioning fails."""


@dataclass(frozen=True)
class AccountCredentials:
    """User account credentials for backend authentication.

    Production mode: User gets JWT tokens, NOT API keys.
    Backend has the API keys, user just authenticates with JWT.
    """
    account_id: str
    email: str
    auth_token: str  # JWT for backend authentication
    refresh_token: str
    telemetry_token: str
    issued_at: Optional[str] = None

    @classmethod
    def from_payload(cls, email: str, payload: Dict[str, Any]) -> "AccountCredentials":
        try:
            # Support both old format (accountId/authToken) and new format (user_id/access_token)
            account_id = str(payload.get("accountId") or payload.get("user_id"))
            auth_token = str(payload.get("authToken") or payload.get("access_token"))

            return cls(
                account_id=account_id,
                email=email,
                auth_token=auth_token,
                refresh_token=str(payload.get("refreshToken") or payload.get("refresh_token") or ""),
                telemetry_token=str(payload.get("telemetryToken") or payload.get("telemetry_token") or ""),
                issued_at=str(payload.get("issuedAt") or payload.get("issued_at") or "") or None,
            )
        except (KeyError, TypeError) as exc:  # pragma: no cover - defensive guard
            raise AccountProvisioningError(
                f"Account provisioning payload missing required fields: {exc!s}"  # noqa: TRY200
            ) from exc


class AccountClient:
    """Minimal client for authenticating against the control plane.

    If ``NOCTURNAL_CONTROL_PLANE_URL`` is unset the client falls back to an
    offline deterministic token generator so local development and CI remain
    hermetic.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: int = 10):
        self.base_url = (
            base_url
            or os.getenv("NOCTURNAL_CONTROL_PLANE_URL")
            or "https://cite-agent-api-720dfadd602c.herokuapp.com"
        )
        self.timeout = timeout

    def provision(self, email: str, password: str) -> AccountCredentials:
        if self.base_url:
            payload = self._request_credentials(email, password)
            return AccountCredentials.from_payload(email=email, payload=payload)
        return self._generate_offline_credentials(email, password)

    # -- internal helpers -------------------------------------------------
    def _request_credentials(self, email: str, password: str) -> Dict[str, Any]:
        try:  # pragma: no cover - requires network
            import requests  # type: ignore
        except Exception as exc:  # pragma: no cover - executed when requests missing
            raise AccountProvisioningError(
                "The 'requests' package is required for control-plane authentication"
            ) from exc

        # Try login first
        login_endpoint = self.base_url.rstrip("/") + "/api/auth/login"
        body = {"email": email, "password": password}

        try:
            response = requests.post(login_endpoint, json=body, timeout=self.timeout)
        except Exception as exc:  # pragma: no cover - network failure
            raise AccountProvisioningError("Failed to reach control plane") from exc

        # If login fails with 401 (user doesn't exist), try registration
        if response.status_code == 401:
            register_endpoint = self.base_url.rstrip("/") + "/api/auth/register"
            try:
                response = requests.post(register_endpoint, json=body, timeout=self.timeout)
            except Exception as exc:
                raise AccountProvisioningError("Failed to register account") from exc

        # If still failing, raise error
        if response.status_code >= 400:
            detail = self._extract_error_detail(response)
            raise AccountProvisioningError(
                f"Authentication failed (status {response.status_code}): {detail}"
            )

        try:
            payload = response.json()
        except ValueError as exc:  # pragma: no cover - invalid JSON
            raise AccountProvisioningError("Control plane returned invalid JSON") from exc

        if not isinstance(payload, dict):  # pragma: no cover - sanity guard
            raise AccountProvisioningError("Control plane response must be an object")
        return payload

    @staticmethod
    def _extract_error_detail(response: Any) -> str:
        try:  # pragma: no cover - best effort decoding
            data = response.json()
            if isinstance(data, dict) and data.get("detail"):
                return str(data["detail"])
        except Exception:
            pass
        return response.text.strip() or "unknown error"

    @staticmethod
    def _generate_offline_credentials(email: str, password: str) -> AccountCredentials:
        seed = f"{email.lower()}::{password}"
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        auth_token = digest[12:44]
        refresh_token = digest[44:]
        telemetry_token = digest[24:56]
        return AccountCredentials(
            account_id=digest[:12],
            email=email,
            auth_token=auth_token,
            refresh_token=refresh_token,
            telemetry_token=telemetry_token,
            issued_at=None,
        )


__all__ = [
    "AccountClient",
    "AccountCredentials",
    "AccountProvisioningError",
]
