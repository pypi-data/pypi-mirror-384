"""
Metrics and health-check client utilities for SPAPS.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

__all__ = ["MetricsClient"]


class MetricsClient:
    """Lightweight client for metrics and health endpoints."""

    def __init__(
        self,
        *,
        base_url: str,
        client: Optional[httpx.Client] = None,
        request_timeout: float | httpx.Timeout = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(base_url=self.base_url, timeout=request_timeout)
        self._owns_client = client is None

    def __enter__(self) -> "MetricsClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore[override]
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def get_prometheus_metrics(self) -> str:
        response = self._client.get("/api/metrics", headers={"Accept": "text/plain"})
        response.raise_for_status()
        return response.text

    def get_metrics_json(self) -> Dict[str, Any]:
        response = self._client.get("/api/metrics/json", headers={"Accept": "application/json"})
        response.raise_for_status()
        return response.json()

    def health(self) -> Dict[str, Any]:
        response = self._client.get("/health")
        response.raise_for_status()
        return response.json()

    def readiness(self) -> Dict[str, Any]:
        response = self._client.get("/health/ready")
        response.raise_for_status()
        return response.json()
