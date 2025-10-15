"""Async secure messages client."""

from __future__ import annotations

from typing import Any, Dict, Optional, List

import httpx

from .secure_messages import SecureMessage, SecureMessagesError


class AsyncSecureMessagesClient:
    SECURE_MESSAGES_PREFIX = "/api/secure-messages"

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

    async def create_message(
        self,
        *,
        patient_id: str,
        practitioner_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        access_token_override: Optional[str] = None,
    ) -> SecureMessage:
        payload: Dict[str, Any] = {"patientId": patient_id, "practitionerId": practitioner_id, "content": content}
        if metadata is not None:
            payload["metadata"] = metadata
        response = await self._client.post(
            self.SECURE_MESSAGES_PREFIX,
            json=payload,
            headers=self._build_headers(access_token_override),
        )
        return await self._parse_message_response(response)

    async def list_messages(self, *, access_token_override: Optional[str] = None) -> List[SecureMessage]:
        response = await self._client.get(
            self.SECURE_MESSAGES_PREFIX,
            headers=self._build_headers(access_token_override),
        )
        payload = await self._parse_payload(response)
        messages = payload.get("messages", [])
        return [SecureMessage.model_validate(item) for item in messages]

    def _build_headers(self, access_token_override: Optional[str]) -> Dict[str, str]:
        headers = {"X-API-Key": self.api_key}
        token = access_token_override or self.access_token
        if token:
            headers["Authorization"] = f"Bearer {token}"
        else:
            raise ValueError("Access token is required for secure message operations")
        return headers

    async def _parse_message_response(self, response: httpx.Response) -> SecureMessage:
        payload = await self._parse_payload(response)
        return SecureMessage.model_validate(payload)

    async def _parse_payload(self, response: httpx.Response) -> Dict[str, Any]:
        if response.status_code >= 400:
            raise await self._build_error(response)
        payload = response.json()
        data = payload.get("data")
        if isinstance(data, dict):
            return data
        return payload

    @staticmethod
    async def _build_error(response: httpx.Response) -> SecureMessagesError:
        try:
            payload = response.json()
        except ValueError:
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


__all__ = ["AsyncSecureMessagesClient"]
