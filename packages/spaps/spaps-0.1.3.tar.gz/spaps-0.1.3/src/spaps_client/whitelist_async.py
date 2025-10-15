"""Async whitelist client mirroring the synchronous implementation."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from .whitelist import (
    WhitelistError,
    WhitelistEntry,
    WhitelistCheckResult,
    WhitelistListResult,
    WhitelistMessage,
)


class AsyncWhitelistClient:
    WHITELIST_PREFIX = "/api/v1/whitelist"

    @staticmethod
    def _as_dict(value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        access_token: Optional[str] = None,
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

    async def check(self, *, email: str) -> WhitelistCheckResult:
        payload = await self._request(method="GET", path="/check", params={"email": email}, require_jwt=False)
        data = self._as_dict(payload.get("data"))
        entry = data.get("entry")
        message = data.get("message") or payload.get("message")
        if not message:
            raise WhitelistError("Whitelist check response missing message", status_code=500)
        result: Dict[str, Any] = {"message": message}
        if isinstance(entry, dict):
            result["entry"] = entry
        return WhitelistCheckResult.model_validate(result)

    async def list(
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
        payload = await self._request(
            method="GET",
            path="",
            params=params,
            require_jwt=True,
            access_token_override=access_token_override,
        )
        data = self._as_dict(payload.get("data"))
        entries = data.get("entries") or []
        total = data.get("total", len(entries))
        return WhitelistListResult.model_validate({"entries": entries, "total": total})

    async def add(
        self,
        *,
        email: str,
        tier: str = "premium",
        bypass_payment: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        access_token_override: Optional[str] = None,
    ) -> WhitelistEntry:
        body: Dict[str, Any] = {"email": email, "tier": tier, "bypass_payment": bypass_payment}
        if metadata is not None:
            body["metadata"] = metadata
        payload = await self._request(
            method="POST",
            path="",
            json=body,
            require_jwt=True,
            access_token_override=access_token_override,
        )
        data = self._as_dict(payload.get("data"))
        entry = data.get("entry")
        if not isinstance(entry, dict):
            raise WhitelistError("Whitelist add response missing entry", status_code=500)
        return WhitelistEntry.model_validate(entry)

    async def update(
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
        payload = await self._request(
            method="PUT",
            path=f"/{email}",
            json=body,
            require_jwt=True,
            access_token_override=access_token_override,
        )
        data = self._as_dict(payload.get("data"))
        entry = data.get("entry")
        if not isinstance(entry, dict):
            raise WhitelistError("Whitelist update response missing entry", status_code=500)
        return WhitelistEntry.model_validate(entry)

    async def remove(
        self,
        *,
        email: str,
        access_token_override: Optional[str] = None,
    ) -> WhitelistMessage:
        payload = await self._request(
            method="DELETE",
            path=f"/{email}",
            require_jwt=True,
            access_token_override=access_token_override,
        )
        data = self._as_dict(payload.get("data"))
        message = data.get("message") or payload.get("message")
        if not message:
            raise WhitelistError("Whitelist remove response missing message", status_code=500)
        return WhitelistMessage.model_validate({"message": message})

    async def _request(
        self,
        *,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        require_jwt: bool,
        access_token_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        headers = {"X-API-Key": self.api_key}
        token = access_token_override or self.access_token
        if require_jwt:
            if not token:
                raise ValueError("This operation requires an access token")
            headers["Authorization"] = f"Bearer {token}"
        response = await self._client.request(
            method,
            f"{self.WHITELIST_PREFIX}{path}",
            params=params,
            json=json,
            headers=headers,
        )
        if response.status_code >= 400:
            raise await self._build_error(response)
        return response.json()

    @staticmethod
    async def _build_error(response: httpx.Response) -> WhitelistError:
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        error = payload.get("error", {})
        message = error.get("message") or response.text or "Whitelist request failed"
        request_id = (
            response.headers.get("x-request-id")
            or payload.get("metadata", {}).get("request_id")
        )
        return WhitelistError(
            message,
            status_code=response.status_code,
            error_code=error.get("code"),
            response=response,
            request_id=request_id,
        )


__all__ = ["AsyncWhitelistClient"]
