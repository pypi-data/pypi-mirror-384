"""Whitelist management helpers for SPAPS."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, ConfigDict

__all__ = [
    "WhitelistClient",
    "WhitelistError",
    "WhitelistEntry",
    "WhitelistCheckResult",
    "WhitelistListResult",
    "WhitelistMessage",
]


class WhitelistError(Exception):
    """Raised when whitelist endpoints return an error."""

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


class WhitelistEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str
    application_id: Optional[str] = None
    tier: Optional[str] = None
    bypass_payment: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class WhitelistCheckResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str
    entry: Optional[WhitelistEntry] = None


class WhitelistListResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    entries: List[WhitelistEntry]
    total: int


class WhitelistMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


class WhitelistClient:
    """Client wrapper for whitelist endpoints."""

    WHITELIST_PREFIX = "/api/v1/whitelist"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        access_token: Optional[str] = None,
        client: Optional[httpx.Client] = None,
        request_timeout: float | httpx.Timeout = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.access_token = access_token
        self._client = client or httpx.Client(base_url=self.base_url, timeout=request_timeout)
        self._owns_client = client is None

    def __enter__(self) -> "WhitelistClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore[override]
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def check(self, *, email: str) -> WhitelistCheckResult:
        payload = self._request(
            method="GET",
            path="/check",
            params={"email": email},
            require_jwt=False,
        )
        data = _as_dict(payload.get("data"))
        entry = data.get("entry")
        message = data.get("message") or payload.get("message")
        if not message:
            raise WhitelistError("Whitelist check response missing message", status_code=500)
        result: Dict[str, Any] = {"message": message}
        if isinstance(entry, dict):
            result["entry"] = entry
        return WhitelistCheckResult.model_validate(result)

    def list(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
        tier: Optional[str] = None,
        access_token_override: Optional[str] = None,
    ) -> WhitelistListResult:
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if tier:
            params["tier"] = tier
        payload = self._request(
            method="GET",
            path="",
            params=params,
            require_jwt=True,
            access_token_override=access_token_override,
        )
        data = _as_dict(payload.get("data"))
        entries = data.get("entries") or []
        total = data.get("total", len(entries))
        return WhitelistListResult.model_validate({
            "entries": entries,
            "total": total,
        })

    def add(
        self,
        *,
        email: str,
        tier: str = "premium",
        bypass_payment: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        access_token_override: Optional[str] = None,
    ) -> WhitelistEntry:
        body: Dict[str, Any] = {
            "email": email,
            "tier": tier,
            "bypass_payment": bypass_payment,
        }
        if metadata is not None:
            body["metadata"] = metadata
        payload = self._request(
            method="POST",
            path="",
            json=body,
            require_jwt=True,
            access_token_override=access_token_override,
        )
        data = _as_dict(payload.get("data"))
        entry = data.get("entry")
        if not isinstance(entry, dict):
            raise WhitelistError("Whitelist add response missing entry", status_code=500)
        return WhitelistEntry.model_validate(entry)

    def update(
        self,
        *,
        email: str,
        tier: Optional[str] = None,
        bypass_payment: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
        access_token_override: Optional[str] = None,
    ) -> WhitelistEntry:
        body: Dict[str, Any] = {}
        if tier is not None:
            body["tier"] = tier
        if bypass_payment is not None:
            body["bypass_payment"] = bypass_payment
        if metadata is not None:
            body["metadata"] = metadata
        payload = self._request(
            method="PUT",
            path=f"/{email}",
            json=body,
            require_jwt=True,
            access_token_override=access_token_override,
        )
        data = _as_dict(payload.get("data"))
        entry = data.get("entry")
        if not isinstance(entry, dict):
            raise WhitelistError("Whitelist update response missing entry", status_code=500)
        return WhitelistEntry.model_validate(entry)

    def remove(
        self,
        *,
        email: str,
        access_token_override: Optional[str] = None,
    ) -> WhitelistMessage:
        payload = self._request(
            method="DELETE",
            path=f"/{email}",
            require_jwt=True,
            access_token_override=access_token_override,
        )
        data = _as_dict(payload.get("data"))
        message = data.get("message") or payload.get("message")
        if not message:
            raise WhitelistError("Whitelist remove response missing message", status_code=500)
        return WhitelistMessage.model_validate({"message": message})

    def _request(
        self,
        *,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        require_jwt: bool,
        access_token_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        headers = {
            "X-API-Key": self.api_key,
        }
        token = access_token_override or self.access_token
        if require_jwt:
            if not token:
                raise ValueError("This operation requires an access token")
            headers["Authorization"] = f"Bearer {token}"
        response = self._client.request(
            method,
            f"{self.WHITELIST_PREFIX}{path}",
            params=params,
            json=json,
            headers=headers,
        )
        if response.status_code >= 400:
            raise self._build_error(response)
        return response.json()

    @staticmethod
    def _build_error(response: httpx.Response) -> WhitelistError:
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        error_info = payload.get("error", {})
        message = error_info.get("message") or response.text or "Whitelist request failed"
        request_id = (
            response.headers.get("x-request-id")
            or payload.get("metadata", {}).get("request_id")
        )
        return WhitelistError(
            message,
            status_code=response.status_code,
            error_code=error_info.get("code"),
            response=response,
            request_id=request_id,
        )
