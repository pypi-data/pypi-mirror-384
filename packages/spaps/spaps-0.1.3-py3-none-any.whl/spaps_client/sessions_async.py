"""Async session client equivalent."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from .sessions import (
    SessionError,
    SessionSummary,
    SessionValidationResult,
    SessionListResult,
    SessionTouchResult,
    SessionRevokeResult,
)


class AsyncSessionsClient:
    SESSIONS_PREFIX = "/api/sessions"

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

    async def get_current_session(self, *, access_token_override: Optional[str] = None) -> SessionSummary:
        data = await self._get("/current", access_token_override=access_token_override)
        session_payload = self._extract_session(data)
        return SessionSummary.model_validate(session_payload)

    async def validate_session(self, *, access_token_override: Optional[str] = None) -> SessionValidationResult:
        data = await self._post("/validate", json={}, access_token_override=access_token_override)
        session_payload = self._extract_session(data)
        return SessionValidationResult.model_validate(session_payload)

    async def list_sessions(
        self,
        *,
        limit: Optional[int] = None,
        starting_after: Optional[str] = None,
        access_token_override: Optional[str] = None,
    ) -> SessionListResult:
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = str(limit)
        if starting_after:
            params["starting_after"] = starting_after
        data = await self._get("", params=params or None, access_token_override=access_token_override)
        sessions_payload = data.get("sessions") or []
        total = data.get("total", len(sessions_payload))
        return SessionListResult.model_validate({"sessions": sessions_payload, "total": total})

    async def touch_session(self, *, access_token_override: Optional[str] = None) -> SessionTouchResult:
        data = await self._post("/touch", json={}, access_token_override=access_token_override)
        return SessionTouchResult.model_validate(data)

    async def revoke_session(self, session_id: str, *, access_token_override: Optional[str] = None) -> SessionRevokeResult:
        if not session_id:
            raise ValueError("session_id is required")
        data = await self._delete(f"/{session_id}", access_token_override=access_token_override)
        return SessionRevokeResult.model_validate(data)

    async def _get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        access_token_override: Optional[str],
    ) -> Dict[str, Any]:
        response = await self._client.get(
            f"{self.SESSIONS_PREFIX}{path}",
            headers=self._build_headers(access_token_override),
            params=params,
        )
        return await self._parse_response(response)

    async def _post(
        self,
        path: str,
        *,
        json: Dict[str, Any],
        access_token_override: Optional[str],
    ) -> Dict[str, Any]:
        response = await self._client.post(
            f"{self.SESSIONS_PREFIX}{path}",
            json=json,
            headers=self._build_headers(access_token_override),
        )
        return await self._parse_response(response)

    async def _delete(self, path: str, *, access_token_override: Optional[str]) -> Dict[str, Any]:
        response = await self._client.delete(
            f"{self.SESSIONS_PREFIX}{path}",
            headers=self._build_headers(access_token_override),
        )
        return await self._parse_response(response)

    def _build_headers(self, access_token_override: Optional[str]) -> Dict[str, str]:
        token = access_token_override or self.access_token
        if not token:
            raise ValueError("Access token is required for session operations")
        return {"X-API-Key": self.api_key, "Authorization": f"Bearer {token}"}

    async def _parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        if response.status_code >= 400:
            raise await self._build_error(response)
        payload = response.json()
        return payload.get("data", payload)

    @staticmethod
    def _extract_session(payload: Dict[str, Any]) -> Dict[str, Any]:
        if "session" in payload:
            return payload["session"]
        return payload

    @staticmethod
    async def _build_error(response: httpx.Response) -> SessionError:
        try:
            payload = response.json()
        except ValueError:  # pragma: no cover
            payload = {}
        error_info = payload.get("error", {})
        message = error_info.get("message") or response.text or "Session request failed"
        request_id = (
            response.headers.get("x-request-id")
            or payload.get("metadata", {}).get("request_id")
        )
        return SessionError(
            message,
            status_code=response.status_code,
            error_code=error_info.get("code"),
            response=response,
            request_id=request_id,
        )


__all__ = ["AsyncSessionsClient"]
