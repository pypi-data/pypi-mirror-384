"""Async usage client mirroring the synchronous UsageClient API."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from .usage import (
    UsageError,
    UsageFeaturesResponse,
    UsageRecordResult,
    UsageHistoryResponse,
)


class AsyncUsageClient:
    USAGE_PREFIX = "/api/usage"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        access_token: str,
        client: Optional[httpx.AsyncClient] = None,
        request_timeout: float | httpx.Timeout = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.access_token = access_token
        self._client = client or httpx.AsyncClient(base_url=self.base_url, timeout=request_timeout)
        self._owns_client = client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def get_features(self, *, access_token_override: Optional[str] = None) -> UsageFeaturesResponse:
        data = await self._get("/features", access_token_override=access_token_override)
        return UsageFeaturesResponse.model_validate(data)

    async def record_usage(
        self,
        *,
        feature: str,
        quantity: float,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        access_token_override: Optional[str] = None,
    ) -> UsageRecordResult:
        payload: Dict[str, Any] = {"feature": feature, "quantity": quantity}
        if metadata is not None:
            payload["metadata"] = metadata
        if timestamp is not None:
            payload["timestamp"] = timestamp
        headers = self._build_headers(access_token_override)
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        response = await self._client.post(f"{self.USAGE_PREFIX}/record", json=payload, headers=headers)
        data = await self._parse_response(response)
        return UsageRecordResult.model_validate(data)

    async def get_history(
        self,
        *,
        period: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        feature: Optional[str] = None,
        format: Optional[str] = None,
        access_token_override: Optional[str] = None,
    ) -> UsageHistoryResponse:
        params: Dict[str, Any] = {}
        if period:
            params["period"] = period
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if feature:
            params["feature"] = feature
        if format:
            params["format"] = format
        data = await self._get(
            "/history",
            params=params or None,
            access_token_override=access_token_override,
        )
        return UsageHistoryResponse.model_validate(data)

    async def _get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        access_token_override: Optional[str],
    ) -> Dict[str, Any]:
        response = await self._client.get(
            f"{self.USAGE_PREFIX}{path}",
            headers=self._build_headers(access_token_override),
            params=params,
        )
        return await self._parse_response(response)

    def _build_headers(self, access_token_override: Optional[str]) -> Dict[str, str]:
        token = access_token_override or self.access_token
        if not token:
            raise ValueError("Access token is required for usage operations")
        return {"X-API-Key": self.api_key, "Authorization": f"Bearer {token}"}

    async def _parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        if response.status_code >= 400:
            raise await self._build_error(response)
        payload = response.json()
        return payload.get("data", payload)

    @staticmethod
    async def _build_error(response: httpx.Response) -> UsageError:
        try:
            payload = response.json()
        except ValueError:  # pragma: no cover
            payload = {}
        error_info = payload.get("error", {})
        message = error_info.get("message") or response.text or "Usage request failed"
        request_id = (
            response.headers.get("x-request-id")
            or payload.get("metadata", {}).get("request_id")
        )
        return UsageError(
            message,
            status_code=response.status_code,
            error_code=error_info.get("code"),
            response=response,
            request_id=request_id,
        )


__all__ = ["AsyncUsageClient"]
