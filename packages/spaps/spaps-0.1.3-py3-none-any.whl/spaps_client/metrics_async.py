"""Async metrics client."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx


class AsyncMetricsClient:
    def __init__(
        self,
        *,
        base_url: str,
        client: Optional[httpx.AsyncClient] = None,
        request_timeout: float | httpx.Timeout = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.AsyncClient(base_url=self.base_url, timeout=request_timeout)
        self._owns_client = client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def get_prometheus_metrics(self) -> str:
        response = await self._client.get("/api/metrics", headers={"Accept": "text/plain"})
        response.raise_for_status()
        return response.text

    async def get_metrics_json(self) -> Dict[str, Any]:
        response = await self._client.get("/api/metrics/json", headers={"Accept": "application/json"})
        response.raise_for_status()
        return response.json()

    async def health(self) -> Dict[str, Any]:
        response = await self._client.get("/health")
        response.raise_for_status()
        return response.json()

    async def readiness(self) -> Dict[str, Any]:
        response = await self._client.get("/health/ready")
        response.raise_for_status()
        return response.json()


__all__ = ["AsyncMetricsClient"]
