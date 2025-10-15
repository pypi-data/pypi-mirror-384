"""
Secure messaging client for SPAPS encrypted communications.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, ConfigDict

__all__ = [
    "SecureMessagesError",
    "SecureMessage",
    "SecureMessagesClient",
]


class SecureMessagesError(Exception):
    """Raised when the secure messages API returns an error."""

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


class SecureMessage(BaseModel):
    """Secure message payload returned by the API."""

    model_config = ConfigDict(extra="ignore")

    id: str
    application_id: Optional[str] = None
    patient_id: str
    practitioner_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


class SecureMessagesClient:
    """Client wrapper for secure messaging endpoints."""

    SECURE_MESSAGES_PREFIX = "/api/secure-messages"

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

    def __enter__(self) -> "SecureMessagesClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore[override]
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def create_message(
        self,
        *,
        patient_id: str,
        practitioner_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        access_token_override: Optional[str] = None,
    ) -> SecureMessage:
        payload: Dict[str, Any] = {
            "patientId": patient_id,
            "practitionerId": practitioner_id,
            "content": content,
        }
        if metadata is not None:
            payload["metadata"] = metadata

        data = self._post(
            "",
            json=payload,
            access_token_override=access_token_override,
        )
        return SecureMessage.model_validate(data)

    def list_messages(
        self,
        *,
        access_token_override: Optional[str] = None,
    ) -> List[SecureMessage]:
        data = self._get("", access_token_override=access_token_override)
        messages_payload = data.get("messages", data)
        return [SecureMessage.model_validate(item) for item in messages_payload]

    # Internal helpers

    def _get(self, path: str, *, access_token_override: Optional[str]) -> Dict[str, Any]:
        response = self._client.get(
            f"{self.SECURE_MESSAGES_PREFIX}{path}",
            headers=self._build_headers(access_token_override),
        )
        return self._parse_response(response)

    def _post(
        self,
        path: str,
        *,
        json: Dict[str, Any],
        access_token_override: Optional[str],
    ) -> Dict[str, Any]:
        response = self._client.post(
            f"{self.SECURE_MESSAGES_PREFIX}{path}",
            json=json,
            headers=self._build_headers(access_token_override),
        )
        return self._parse_response(response)

    def _build_headers(self, access_token_override: Optional[str]) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "X-API-Key": self.api_key,
        }
        token = access_token_override or self.access_token
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @staticmethod
    def _parse_response(response: httpx.Response) -> Dict[str, Any]:
        if response.status_code >= 400:
            raise SecureMessagesClient._build_error(response)
        payload = response.json()
        return payload.get("data", payload)

    @staticmethod
    def _build_error(response: httpx.Response) -> SecureMessagesError:
        try:
            payload = response.json()
        except ValueError:  # pragma: no cover
            payload = {}
        error_info = payload.get("error", {})
        message = error_info.get("message") or response.text or "Secure message request failed"
        request_id = (
            response.headers.get("x-request-id")
            or payload.get("metadata", {}).get("request_id")
        )
        return SecureMessagesError(
            message,
            status_code=response.status_code,
            error_code=error_info.get("code"),
            response=response,
            request_id=request_id,
        )
