"""Async crypto helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from .crypto import (
    CryptoPaymentsError,
    CryptoInvoice,
    CryptoInvoiceStatus,
    CryptoReconcileJob,
)


class AsyncCryptoPaymentsClient:
    CRYPTO_PREFIX = "/api/payments/crypto"

    def __init__(
        self,
        *,
        client: httpx.AsyncClient,
        header_builder,
    ) -> None:
        self._client = client
        self._build_headers = header_builder

    async def create_invoice(
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
        payload: Dict[str, Any] = {"asset": asset, "network": network, "amount": amount}
        if expires_in_seconds is not None:
            payload["expires_in_seconds"] = expires_in_seconds
        if beneficiary is not None:
            payload["beneficiary"] = beneficiary
        if metadata is not None:
            payload["metadata"] = metadata
        data = await self._post("/invoices", json=payload, access_token_override=access_token_override)
        invoice_payload = data.get("invoice", data)
        return CryptoInvoice.model_validate(invoice_payload)

    async def get_invoice(
        self,
        invoice_id: str,
        *,
        access_token_override: Optional[str] = None,
    ) -> CryptoInvoice:
        data = await self._get(f"/invoices/{invoice_id}", access_token_override=access_token_override)
        invoice_payload = data.get("invoice", data)
        return CryptoInvoice.model_validate(invoice_payload)

    async def get_invoice_status(
        self,
        invoice_id: str,
        *,
        access_token_override: Optional[str] = None,
    ) -> CryptoInvoiceStatus:
        data = await self._get(f"/invoices/{invoice_id}/status", access_token_override=access_token_override)
        return CryptoInvoiceStatus.model_validate(data)

    async def reconcile(
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
        response = await self._client.post(
            f"{self.CRYPTO_PREFIX}/reconcile",
            json=payload,
            headers=headers,
        )
        data = await self._parse_response(response)
        return CryptoReconcileJob.model_validate(data)

    async def _get(self, path: str, *, access_token_override: Optional[str]) -> Dict[str, Any]:
        response = await self._client.get(
            f"{self.CRYPTO_PREFIX}{path}",
            headers=self._build_headers(access_token_override),
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
            f"{self.CRYPTO_PREFIX}{path}",
            json=json,
            headers=self._build_headers(access_token_override),
        )
        return await self._parse_response(response)

    @staticmethod
    async def _parse_response(response: httpx.Response) -> Dict[str, Any]:
        if response.status_code >= 400:
            raise await AsyncCryptoPaymentsClient._build_error(response)
        payload = response.json()
        return payload.get("data", payload)

    @staticmethod
    async def _build_error(response: httpx.Response) -> CryptoPaymentsError:
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        error_info = payload.get("error", {})
        message = error_info.get("message") or response.text or "Crypto payments request failed"
        return CryptoPaymentsError(
            message,
            status_code=response.status_code,
            error_code=error_info.get("code"),
            response=response,
        )


__all__ = ["AsyncCryptoPaymentsClient"]
