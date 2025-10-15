"""Telemetry pipeline for the Nocturnal Archive beta."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_LOCK = threading.Lock()
_MANAGER: Optional["TelemetryManager"] = None


class TelemetryManager:
    """JSONL telemetry writer with optional control-plane streaming."""

    def __init__(self, log_path: Path, telemetry_token: Optional[str]):
        self.log_path = log_path
        self.telemetry_token = telemetry_token
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _from_environment(cls) -> "TelemetryManager":
        root = Path(os.getenv("NOCTURNAL_HOME", str(Path.home() / ".nocturnal_archive")))
        log_dir = root / "logs"
        log_path = log_dir / "beta-telemetry.jsonl"
        token = os.getenv("NOCTURNAL_TELEMETRY_TOKEN") or None
        return cls(log_path=log_path, telemetry_token=token)

    @classmethod
    def get(cls) -> "TelemetryManager":
        global _MANAGER
        if _MANAGER is None:
            _MANAGER = cls._from_environment()
        return _MANAGER

    @classmethod
    def refresh(cls) -> None:
        """Force re-reading environment configuration."""
        global _MANAGER
        _MANAGER = cls._from_environment()

    def record(self, event_type: str, payload: Dict[str, Any]) -> None:
        record = {
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        try:
            with _LOCK:
                with self.log_path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            # Telemetry must never break the agent; swallow errors silently.
            pass
        self._send_remote(record)

    def _send_remote(self, record: Dict[str, Any]) -> None:
        endpoint = os.getenv("NOCTURNAL_TELEMETRY_ENDPOINT")
        if not endpoint:
            return
        try:  # pragma: no cover - network integration best effort
            import requests  # type: ignore
        except Exception:
            return
        headers = {}
        if self.telemetry_token:
            headers["Authorization"] = f"Bearer {self.telemetry_token}"
        try:  # pragma: no cover - network integration best effort
            requests.post(
                endpoint.rstrip("/") + "/ingest",
                json=record,
                headers=headers,
                timeout=float(os.getenv("NOCTURNAL_TELEMETRY_TIMEOUT", "5")),
            )
        except Exception:
            # Remote telemetry failures are non-fatal; we rely on local logs for replay.
            pass


def disable_telemetry() -> None:
    """Backward-compatible shim; telemetry is now always-on."""
    TelemetryManager.refresh()