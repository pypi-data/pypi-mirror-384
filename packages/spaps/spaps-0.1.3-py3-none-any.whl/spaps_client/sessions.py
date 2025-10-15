"""
Session management helpers for the Sweet Potato Authentication & Payment Service.

The SessionsClient wraps SPAPS session endpoints, providing helpers to retrieve
the current session metadata and validate/refresh active sessions.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "SessionError",
    "SessionSummary",
    "SessionValidationResult",
    "SessionListResult",
    "SessionRecord",
    "SessionTouchResult",
    "SessionRevokeResult",
    "SessionsClient",
]


class SessionError(Exception):
    """Raised when the SPAPS sessions API returns an error response."""

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


class SessionSummary(BaseModel):
    """Metadata for the current session."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    session_id: str = Field(alias="id")
    user_id: str
    application_id: str
    tier: Optional[str] = None
    created_at: dt.datetime
    expires_at: dt.datetime
    last_activity: dt.datetime
    wallets_count: Optional[int] = None
    duration_minutes: Optional[int] = None
    idle_minutes: Optional[int] = None


class SessionValidationResult(BaseModel):
    """Result of validating an access token/session."""

    model_config = ConfigDict(extra="ignore")

    valid: bool
    session_id: Optional[str] = None
    expires_at: Optional[dt.datetime] = None
    renewed: Optional[bool] = None


class SessionRecord(BaseModel):
    """Active session metadata returned from the list endpoint."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    session_id: str = Field(alias="id")
    user_id: str
    application_id: str
    created_at: dt.datetime
    expires_at: Optional[dt.datetime] = None
    last_used: Optional[dt.datetime] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    is_current: Optional[bool] = None


class SessionListResult(BaseModel):
    """Paginated list of active sessions for the current user."""

    model_config = ConfigDict(extra="ignore")

    sessions: list[SessionRecord] = Field(default_factory=list)
    total: int = 0


class SessionTouchResult(BaseModel):
    """Result of touching a session to update activity."""

    model_config = ConfigDict(extra="ignore")

    message: str
    session_id: str
    last_activity: Optional[dt.datetime] = None


class SessionRevokeResult(BaseModel):
    """Result of revoking a specific session."""

    model_config = ConfigDict(extra="ignore")

    message: str
    session_id: str


class SessionsClient:
    """Client wrapper for SPAPS session endpoints."""

    SESSIONS_PREFIX = "/api/sessions"

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

    def __enter__(self) -> "SessionsClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore[override]
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    # Public API

    def get_current_session(self, *, access_token_override: Optional[str] = None) -> SessionSummary:
        data = self._get("/current", access_token_override=access_token_override)
        session_payload = self._extract_session(data)
        return SessionSummary.model_validate(session_payload)

    def validate_session(self, *, access_token_override: Optional[str] = None) -> SessionValidationResult:
        data = self._post("/validate", json={}, access_token_override=access_token_override)
        session_payload = self._extract_session(data)
        return SessionValidationResult.model_validate(session_payload)

    def list_sessions(
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
        data = self._get(
            "",
            params=params or None,
            access_token_override=access_token_override,
        )
        sessions_payload = data.get("sessions") or []
        total = data.get("total", len(sessions_payload))
        return SessionListResult.model_validate(
            {
                "sessions": sessions_payload,
                "total": total,
            }
        )

    def touch_session(self, *, access_token_override: Optional[str] = None) -> SessionTouchResult:
        data = self._post("/touch", json={}, access_token_override=access_token_override)
        return SessionTouchResult.model_validate(data)

    def revoke_session(self, session_id: str, *, access_token_override: Optional[str] = None) -> SessionRevokeResult:
        if not session_id:
            raise ValueError("session_id is required")
        data = self._delete(f"/{session_id}", access_token_override=access_token_override)
        return SessionRevokeResult.model_validate(data)

    # Internal helpers

    def _get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        access_token_override: Optional[str],
    ) -> Dict[str, Any]:
        response = self._client.get(
            f"{self.SESSIONS_PREFIX}{path}",
            headers=self._build_headers(access_token_override),
            params=params,
        )
        return self._parse_response(response)

    def _post(self, path: str, *, json: Dict[str, Any], access_token_override: Optional[str]) -> Dict[str, Any]:
        response = self._client.post(
            f"{self.SESSIONS_PREFIX}{path}",
            json=json,
            headers=self._build_headers(access_token_override),
        )
        return self._parse_response(response)

    def _delete(self, path: str, *, access_token_override: Optional[str]) -> Dict[str, Any]:
        response = self._client.delete(
            f"{self.SESSIONS_PREFIX}{path}",
            headers=self._build_headers(access_token_override),
        )
        return self._parse_response(response)

    def _build_headers(self, access_token_override: Optional[str]) -> Dict[str, str]:
        token = access_token_override or self.access_token
        if not token:
            raise ValueError("Access token is required for session operations")
        return {
            "X-API-Key": self.api_key,
            "Authorization": f"Bearer {token}",
        }

    def _parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        if response.status_code >= 400:
            raise self._build_error(response)
        payload = response.json()
        return payload.get("data", payload)

    @staticmethod
    def _extract_session(payload: Dict[str, Any]) -> Dict[str, Any]:
        if "session" in payload:
            return payload["session"]
        return payload

    @staticmethod
    def _build_error(response: httpx.Response) -> SessionError:
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
