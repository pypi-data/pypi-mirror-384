"""
Usage tracking client for the Sweet Potato Authentication & Payment Service.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "UsageError",
    "UsagePeriod",
    "UsageFeature",
    "UsageFeaturesResponse",
    "UsageRecordUsage",
    "UsageRecordResult",
    "UsageHistoryEntry",
    "UsageHistoryResponse",
    "UsageClient",
]


class UsageError(Exception):
    """Raised when the usage API returns an error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        error_code: Optional[str] = None,
        response: Optional[httpx.Response] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.response = response
        self.request_id = request_id


class UsagePeriod(BaseModel):
    """Billing period bounds."""

    model_config = ConfigDict(extra="ignore")

    start: Optional[str] = None
    end: Optional[str] = None


class UsageFeature(BaseModel):
    """Usage metadata for a single feature."""

    model_config = ConfigDict(extra="ignore")

    name: str
    description: Optional[str] = None
    used: Optional[float] = None
    limit: Optional[float] = None
    percentage: Optional[float] = None
    reset_at: Optional[str] = None


class UsageFeaturesResponse(BaseModel):
    """Usage overview response payload."""

    model_config = ConfigDict(extra="ignore")

    user_id: Optional[str] = None
    tier: Optional[str] = None
    period: UsagePeriod = Field(default_factory=UsagePeriod)
    features: list[UsageFeature] = Field(default_factory=list)
    overage: Optional[Dict[str, Any]] = None


class UsageRecordUsage(BaseModel):
    """Current usage after recording an event."""

    model_config = ConfigDict(extra="ignore")

    used: Optional[float] = None
    limit: Optional[float] = None
    remaining: Optional[float] = None


class UsageRecordResult(BaseModel):
    """Result of recording usage."""

    model_config = ConfigDict(extra="ignore")

    record_id: str
    feature: str
    quantity: Optional[float] = None
    recorded_at: Optional[str] = None
    current_usage: UsageRecordUsage = Field(default_factory=UsageRecordUsage)
    warning: Optional[str] = None


class UsageHistoryEntry(BaseModel):
    """Aggregated usage entry."""

    model_config = ConfigDict(extra="ignore")

    date: Optional[str] = None
    features: Dict[str, Any] = Field(default_factory=dict)
    total_cost: Optional[float] = None


class UsageHistoryResponse(BaseModel):
    """Usage history response with summary statistics."""

    model_config = ConfigDict(extra="ignore")

    period: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    history: list[UsageHistoryEntry] = Field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None


class UsageClient:
    """Client wrapper for usage endpoints."""

    USAGE_PREFIX = "/api/usage"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        access_token: str,
        client: Optional[httpx.Client] = None,
        request_timeout: float | httpx.Timeout = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.access_token = access_token
        self._client = client or httpx.Client(base_url=self.base_url, timeout=request_timeout)
        self._owns_client = client is None

    def __enter__(self) -> "UsageClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore[override]
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def get_features(self, *, access_token_override: Optional[str] = None) -> UsageFeaturesResponse:
        data = self._get("/features", access_token_override=access_token_override)
        return UsageFeaturesResponse.model_validate(data)

    def record_usage(
        self,
        *,
        feature: str,
        quantity: float,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        access_token_override: Optional[str] = None,
    ) -> UsageRecordResult:
        payload: Dict[str, Any] = {
            "feature": feature,
            "quantity": quantity,
        }
        if metadata is not None:
            payload["metadata"] = metadata
        if timestamp is not None:
            payload["timestamp"] = timestamp
        headers = self._build_headers(access_token_override)
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key

        response = self._client.post(
            f"{self.USAGE_PREFIX}/record",
            json=payload,
            headers=headers,
        )
        data = self._parse_response(response)
        return UsageRecordResult.model_validate(data)

    def get_history(
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

        data = self._get(
            "/history",
            params=params or None,
            access_token_override=access_token_override,
        )
        return UsageHistoryResponse.model_validate(data)

    # Internal helpers

    def _get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        access_token_override: Optional[str],
    ) -> Dict[str, Any]:
        response = self._client.get(
            f"{self.USAGE_PREFIX}{path}",
            headers=self._build_headers(access_token_override),
            params=params,
        )
        return self._parse_response(response)

    def _build_headers(self, access_token_override: Optional[str]) -> Dict[str, str]:
        token = access_token_override or self.access_token
        if not token:
            raise ValueError("Access token is required for usage operations")
        return {
            "X-API-Key": self.api_key,
            "Authorization": f"Bearer {token}",
        }

    @staticmethod
    def _parse_response(response: httpx.Response) -> Dict[str, Any]:
        if response.status_code >= 400:
            raise UsageClient._build_error(response)
        payload = response.json()
        return payload.get("data", payload)

    @staticmethod
    def _build_error(response: httpx.Response) -> UsageError:
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
