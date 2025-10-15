"""
Crypto payments helpers and webhook signature utilities for SPAPS.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any, Callable, Dict, Optional

import httpx
from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CryptoPaymentsError",
    "CryptoInvoice",
    "CryptoInvoiceStatus",
    "CryptoReconcileJob",
    "CryptoPaymentsClient",
    "verify_crypto_webhook_signature",
]


class CryptoPaymentsError(Exception):
    """Raised when crypto payments endpoints return an error."""

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


class CryptoInvoice(BaseModel):
    """Metadata describing a crypto invoice."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    invoice_id: str = Field(alias="id")
    asset: str
    network: str
    amount: str
    status: str
    expires_at: Optional[str] = None
    beneficiary: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class CryptoInvoiceStatus(BaseModel):
    """Snapshot information about a crypto invoice settlement status."""

    model_config = ConfigDict(extra="ignore")

    invoice_id: str
    status: str
    finalized_at: Optional[str] = None
    normalized_amount: Optional[str] = None
    settlement_ids: Optional[list[str]] = None
    underpaid: Optional[bool] = None
    overpaid: Optional[bool] = None


class CryptoReconcileJob(BaseModel):
    """Response payload after scheduling a reconcile job."""

    model_config = ConfigDict(extra="ignore")

    job_id: str
    scheduled_at: str
    cursor: Optional[Dict[str, Any]] = None


class CryptoPaymentsClient:
    """Client wrapper for SPAPS crypto invoice endpoints."""

    CRYPTO_PREFIX = "/api/payments/crypto"

    def __init__(
        self,
        *,
        client: httpx.Client,
        header_builder: Callable[[Optional[str]], Dict[str, str]],
    ) -> None:
        self._client = client
        self._build_headers = header_builder

    def create_invoice(
        self,
        *,
        asset: str,
        network: str,
        amount: str,
        expires_in_seconds: Optional[int] = None,
        beneficiary: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        access_token_override: Optional[str] = None,
    ) -> CryptoInvoice:
        payload: Dict[str, Any] = {
            "asset": asset,
            "network": network,
            "amount": amount,
        }
        if expires_in_seconds is not None:
            payload["expires_in_seconds"] = expires_in_seconds
        if beneficiary is not None:
            payload["beneficiary"] = beneficiary
        if metadata is not None:
            payload["metadata"] = metadata

        data = self._post(
            "/invoices",
            json=payload,
            access_token_override=access_token_override,
        )
        invoice_payload = data.get("invoice", data)
        return CryptoInvoice.model_validate(invoice_payload)

    def get_invoice(
        self,
        invoice_id: str,
        *,
        access_token_override: Optional[str] = None,
    ) -> CryptoInvoice:
        data = self._get(
            self._invoice_path(invoice_id),
            access_token_override=access_token_override,
        )
        invoice_payload = data.get("invoice", data)
        return CryptoInvoice.model_validate(invoice_payload)

    def get_invoice_status(
        self,
        invoice_id: str,
        *,
        access_token_override: Optional[str] = None,
    ) -> CryptoInvoiceStatus:
        data = self._get(
            f"{self._invoice_path(invoice_id)}/status",
            access_token_override=access_token_override,
        )
        return CryptoInvoiceStatus.model_validate(data)

    def reconcile(
        self,
        *,
        recon_token: Optional[str] = None,
        cursor: Optional[Dict[str, Any]] = None,
        access_token_override: Optional[str] = None,
    ) -> CryptoReconcileJob:
        headers = self._build_headers(access_token_override)
        if recon_token:
            headers = {**headers, "X-Recon-Token": recon_token}

        payload: Dict[str, Any] = {}
        if cursor is not None:
            payload["cursor"] = cursor

        response = self._client.post(
            f"{self.CRYPTO_PREFIX}/reconcile",
            json=payload,
            headers=headers,
        )
        data = self._parse_response(response)
        return CryptoReconcileJob.model_validate(data)

    # Internal helpers

    def _get(self, path: str, *, access_token_override: Optional[str]) -> Dict[str, Any]:
        response = self._client.get(
            f"{self.CRYPTO_PREFIX}{path}",
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
            f"{self.CRYPTO_PREFIX}{path}",
            json=json,
            headers=self._build_headers(access_token_override),
        )
        return self._parse_response(response)

    @staticmethod
    def _parse_response(response: httpx.Response) -> Dict[str, Any]:
        if response.status_code >= 400:
            raise CryptoPaymentsClient._build_error(response)
        payload = response.json()
        return payload.get("data", payload)

    @staticmethod
    def _build_error(response: httpx.Response) -> CryptoPaymentsError:
        try:
            payload = response.json()
        except ValueError:  # pragma: no cover
            payload = {}
        error_info = payload.get("error", {})
        message = error_info.get("message") or response.text or "Crypto payments request failed"
        request_id = (
            response.headers.get("x-request-id")
            or payload.get("metadata", {}).get("request_id")
        )
        return CryptoPaymentsError(
            message,
            status_code=response.status_code,
            error_code=error_info.get("code"),
            response=response,
            request_id=request_id,
        )

    @classmethod
    def _invoice_path(cls, invoice_id: str, *, include_prefix: bool = False) -> str:
        """
        Return the relative API path for an invoice resource.

        Set ``include_prefix=True`` to include the crypto base path, useful when logging fully
        qualified URLs outside of the internal helpers.
        """
        relative = f"/invoices/{invoice_id}"
        return f"{cls.CRYPTO_PREFIX}{relative}" if include_prefix else relative


def verify_crypto_webhook_signature(
    *,
    body: Any,
    signature: str,
    secret: str,
    tolerance_seconds: int = 300,
) -> bool:
    """
    Verify an HMAC-based crypto webhook signature.

    Expects signatures in the format ``t=<timestamp>,v1=<hmac>`` where ``hmac`` is
    computed as ``sha256(secret, f"{timestamp}.{raw_body}")``.
    """

    if not signature:
        raise ValueError("Missing webhook signature")

    parts: Dict[str, str] = {}
    for element in signature.split(","):
        key, _, value = element.partition("=")
        if key and value:
            parts[key.strip()] = value.strip()

    timestamp = parts.get("t")
    expected = parts.get("v1")

    if not timestamp or not expected:
        raise ValueError("Invalid webhook signature format")

    if isinstance(body, (bytes, bytearray)):
        body_bytes = bytes(body)
    elif isinstance(body, str):
        body_bytes = body.encode("utf-8")
    else:
        raise ValueError("Expected body to be the raw request body as str or bytes.")

    payload = timestamp.encode("utf-8") + b"." + body_bytes
    computed_bytes = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()

    expected_bytes = bytes.fromhex(expected)

    if len(expected_bytes) != len(computed_bytes) or not hmac.compare_digest(expected_bytes, computed_bytes):
        raise ValueError("Invalid webhook signature")

    ts_value = int(timestamp)
    if tolerance_seconds > 0:
        now = int(time.time())
        if abs(now - ts_value) > tolerance_seconds:
            raise ValueError("Webhook signature timestamp outside tolerance window")

    return True
