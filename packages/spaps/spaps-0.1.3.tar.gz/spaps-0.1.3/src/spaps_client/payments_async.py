"""
Async payments client mirroring the synchronous PaymentsClient API.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from .payments import (
    PaymentsError,
    CheckoutSession,
    CheckoutSessionDetails,
    CheckoutSessionList,
    ExpireCheckoutSessionResult,
    PaymentIntent,
    WalletDeposit,
    WalletTransaction,
    SubscriptionDetail,
    SubscriptionCancellation,
    SubscriptionList,
    BalanceOverview,
    PaymentMethodUpdateResult,
    ProductList,
    Product,
    GuestCheckoutSession,
    GuestCheckoutSessionList,
    GuestCheckoutConversionResult,
    PaymentHistory,
    PaymentRecord,
)
from .crypto_async import AsyncCryptoPaymentsClient


class AsyncPaymentsClient:
    PAYMENTS_PREFIX = "/api/payments"
    STRIPE_PREFIX = "/api/stripe"

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
        self.crypto = AsyncCryptoPaymentsClient(client=self._client, header_builder=self._build_headers)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def create_checkout_session(
        self,
        *,
        price_id: str,
        mode: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None,
        access_token_override: Optional[str] = None,
    ) -> CheckoutSession:
        payload: Dict[str, Any] = {
            "price_id": price_id,
            "mode": mode,
            "success_url": success_url,
            "cancel_url": cancel_url,
        }
        if metadata:
            payload["metadata"] = metadata
        data = await self._post(
            "/create-checkout-session",
            json=payload,
            access_token_override=access_token_override,
        )
        return CheckoutSession.model_validate(data)

    async def get_balance(self, *, access_token_override: Optional[str] = None) -> BalanceOverview:
        data = await self._get("/balance", access_token_override=access_token_override)
        return BalanceOverview.model_validate(data)

    async def create_payment_intent(
        self,
        *,
        amount: int,
        currency: str,
        payment_method_types: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        access_token_override: Optional[str] = None,
    ) -> PaymentIntent:
        payload: Dict[str, Any] = {"amount": amount, "currency": currency}
        if payment_method_types is not None:
            payload["payment_method_types"] = payment_method_types
        if metadata:
            payload["metadata"] = metadata
        data = await self._post(
            "/create-payment-intent",
            json=payload,
            access_token_override=access_token_override,
        )
        return PaymentIntent.model_validate(data)

    async def update_payment_method(
        self,
        *,
        payment_method_id: str,
        set_default: Optional[bool] = None,
        access_token_override: Optional[str] = None,
    ) -> PaymentMethodUpdateResult:
        if not payment_method_id:
            raise ValueError("payment_method_id is required")
        payload: Dict[str, Any] = {"payment_method_id": payment_method_id}
        if set_default is not None:
            payload["set_default"] = set_default
        data = await self._post(
            "/update-payment-method",
            json=payload,
            access_token_override=access_token_override,
        )
        return PaymentMethodUpdateResult.model_validate(data)

    async def wallet_deposit(
        self,
        *,
        wallet_address: str,
        chain_type: str,
        transaction_id: str,
        amount: float,
        currency: str,
        tier: Optional[str] = None,
        access_token_override: Optional[str] = None,
    ) -> WalletDeposit:
        payload: Dict[str, Any] = {
            "wallet_address": wallet_address,
            "chain_type": chain_type,
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
        }
        if tier:
            payload["tier"] = tier
        data = await self._post(
            "/wallet-deposit",
            json=payload,
            access_token_override=access_token_override,
        )
        return WalletDeposit.model_validate(data)

    async def get_wallet_transaction(
        self,
        *,
        transaction_id: str,
        access_token_override: Optional[str] = None,
    ) -> WalletTransaction:
        data = await self._get(
            f"/wallet-transaction/{transaction_id}",
            access_token_override=access_token_override,
        )
        return WalletTransaction.model_validate(data)

    async def get_subscription(
        self,
        *,
        subscription_id: str,
        access_token_override: Optional[str] = None,
    ) -> SubscriptionDetail:
        data = await self._get_stripe(
            f"/subscription/{subscription_id}",
            params=None,
            access_token_override=access_token_override,
        )
        return SubscriptionDetail.model_validate(data)

    async def list_subscriptions(
        self,
        *,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        starting_after: Optional[str] = None,
        access_token_override: Optional[str] = None,
    ) -> SubscriptionList:
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        if limit is not None:
            params["limit"] = str(limit)
        if starting_after:
            params["starting_after"] = starting_after

        data = await self._get_stripe(
            "/subscriptions",
            params=params or None,
            access_token_override=access_token_override,
        )
        return SubscriptionList.model_validate(data)

    async def cancel_subscription(
        self,
        *,
        subscription_id: str,
        immediately: Optional[bool] = None,
        access_token_override: Optional[str] = None,
    ) -> SubscriptionCancellation:
        payload: Dict[str, Any] = {}
        if immediately is not None:
            payload["immediately"] = immediately
        data = await self._post_stripe(
            f"/subscription/{subscription_id}/cancel",
            json=payload,
            access_token_override=access_token_override,
        )
        return SubscriptionCancellation.model_validate(data)

    async def update_subscription(
        self,
        *,
        subscription_id: str,
        price_id: str,
        access_token_override: Optional[str] = None,
    ) -> SubscriptionDetail:
        if not price_id:
            raise ValueError("price_id is required")
        data = await self._post_stripe(
            f"/subscription/{subscription_id}/update",
            json={"price_id": price_id},
            access_token_override=access_token_override,
        )
        return SubscriptionDetail.model_validate(data)

    async def get_checkout_session(
        self,
        *,
        session_id: str,
        access_token_override: Optional[str] = None,
    ) -> CheckoutSessionDetails:
        data = await self._get_stripe(
            f"/checkout-sessions/{session_id}",
            params=None,
            access_token_override=access_token_override,
        )
        return CheckoutSessionDetails.model_validate(data)

    async def list_checkout_sessions(
        self,
        *,
        limit: Optional[int] = None,
        starting_after: Optional[str] = None,
        access_token_override: Optional[str] = None,
    ) -> CheckoutSessionList:
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = str(limit)
        if starting_after:
            params["starting_after"] = starting_after
        data = await self._get_stripe(
            "/checkout-sessions",
            params=params or None,
            access_token_override=access_token_override,
        )
        return CheckoutSessionList.model_validate(data)

    async def expire_checkout_session(
        self,
        *,
        session_id: str,
        access_token_override: Optional[str] = None,
    ) -> ExpireCheckoutSessionResult:
        data = await self._post_stripe(
            f"/checkout-sessions/{session_id}/expire",
            json={},
            access_token_override=access_token_override,
        )
        return ExpireCheckoutSessionResult.model_validate(data)

    async def create_guest_checkout_session(
        self,
        *,
        customer_email: str,
        mode: str,
        line_items: list[Dict[str, Any]],
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, str]] = None,
        client_reference_id: Optional[str] = None,
        payment_intent_data: Optional[Dict[str, Any]] = None,
        subscription_data: Optional[Dict[str, Any]] = None,
        allow_promotion_codes: Optional[bool] = None,
        locale: Optional[str] = None,
    ) -> GuestCheckoutSession:
        if not customer_email:
            raise ValueError("customer_email is required for guest checkout")
        if not line_items:
            raise ValueError("at least one line item is required")
        payload: Dict[str, Any] = {
            "customer_email": customer_email,
            "mode": mode,
            "line_items": line_items,
            "success_url": success_url,
            "cancel_url": cancel_url,
        }
        if metadata:
            payload["metadata"] = metadata
        if client_reference_id:
            payload["client_reference_id"] = client_reference_id
        if payment_intent_data:
            payload["payment_intent_data"] = payment_intent_data
        if subscription_data:
            payload["subscription_data"] = subscription_data
        if allow_promotion_codes is not None:
            payload["allow_promotion_codes"] = allow_promotion_codes
        if locale:
            payload["locale"] = locale

        data = await self._post_stripe(
            "/guest-checkout-sessions",
            json=payload,
            access_token_override=None,
            require_auth=False,
        )
        return GuestCheckoutSession.model_validate(data)

    async def get_guest_checkout_session(self, *, session_id: str) -> CheckoutSessionDetails:
        data = await self._get_stripe(
            f"/guest-checkout-sessions/{session_id}",
            params=None,
            access_token_override=None,
            require_auth=False,
        )
        return CheckoutSessionDetails.model_validate(data)

    async def list_guest_checkout_sessions(
        self,
        *,
        limit: Optional[int] = None,
        starting_after: Optional[str] = None,
        customer_email: Optional[str] = None,
    ) -> GuestCheckoutSessionList:
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = str(limit)
        if starting_after:
            params["starting_after"] = starting_after
        if customer_email:
            params["customer_email"] = customer_email

        data = await self._get_stripe(
            "/guest-checkout-sessions",
            params=params or None,
            access_token_override=None,
            require_auth=False,
        )
        return GuestCheckoutSessionList.model_validate(data)

    async def convert_guest_checkout_session(
        self,
        *,
        session_id: str,
        email: str,
        password: Optional[str] = None,
        send_magic_link: Optional[bool] = None,
    ) -> GuestCheckoutConversionResult:
        payload: Dict[str, Any] = {
            "session_id": session_id,
            "email": email,
        }
        if password:
            payload["password"] = password
        if send_magic_link is not None:
            payload["send_magic_link"] = send_magic_link

        data = await self._post_stripe(
            "/guest-checkout-sessions/convert",
            json=payload,
            access_token_override=None,
            require_auth=False,
        )
        return GuestCheckoutConversionResult.model_validate(data)

    async def list_payment_history(
        self,
        *,
        limit: Optional[int] = None,
        starting_after: Optional[str] = None,
        ending_before: Optional[str] = None,
        status: Optional[str] = None,
        access_token_override: Optional[str] = None,
    ) -> PaymentHistory:
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = str(limit)
        if starting_after:
            params["starting_after"] = starting_after
        if ending_before:
            params["ending_before"] = ending_before
        if status:
            params["status"] = status

        data = await self._get_stripe(
            "/history",
            params=params or None,
            access_token_override=access_token_override,
        )
        return PaymentHistory.model_validate(data)

    async def get_payment_detail(
        self,
        *,
        payment_id: str,
        access_token_override: Optional[str] = None,
    ) -> PaymentRecord:
        data = await self._get_stripe(
            f"/payment/{payment_id}",
            params=None,
            access_token_override=access_token_override,
        )
        if isinstance(data, dict) and "payment" in data:
            return PaymentRecord.model_validate(data["payment"])
        return PaymentRecord.model_validate(data)

    async def list_products(
        self,
        *,
        category: Optional[str] = None,
        active: Optional[bool] = None,
        limit: Optional[int] = None,
        starting_after: Optional[str] = None,
        mode: Optional[str] = None,
        access_token_override: Optional[str] = None,
    ) -> ProductList:
        params: Dict[str, Any] = {}
        if category:
            params["category"] = category
        if active is not None:
            params["active"] = "true" if active else "false"
        if limit is not None:
            params["limit"] = str(limit)
        if starting_after:
            params["starting_after"] = starting_after
        if mode:
            params["mode"] = mode

        data = await self._get_stripe(
            "/products",
            params=params or None,
            access_token_override=access_token_override,
        )
        return ProductList.model_validate(data)

    async def get_product(
        self,
        *,
        product_id: str,
        include_prices: bool = True,
        access_token_override: Optional[str] = None,
    ) -> Product:
        if not product_id:
            raise ValueError("product_id is required")
        params: Optional[Dict[str, Any]] = None
        if not include_prices:
            params = {"include_prices": "false"}

        data = await self._get_stripe(
            f"/products/{product_id}",
            params=params,
            access_token_override=access_token_override,
        )
        return Product.model_validate(data)

    async def _get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        access_token_override: Optional[str],
    ) -> Dict[str, Any]:
        response = await self._client.get(
            f"{self.PAYMENTS_PREFIX}{path}",
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
            f"{self.PAYMENTS_PREFIX}{path}",
            json=json,
            headers=self._build_headers(access_token_override),
        )
        return await self._parse_response(response)

    async def _get_stripe(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]],
        access_token_override: Optional[str],
        require_auth: bool = True,
    ) -> Dict[str, Any]:
        response = await self._client.get(
            f"{self.STRIPE_PREFIX}{path}",
            params=params,
            headers=self._build_headers(access_token_override, require_auth=require_auth),
        )
        return await self._parse_response(response)

    async def _post_stripe(
        self,
        path: str,
        *,
        json: Dict[str, Any],
        access_token_override: Optional[str],
        require_auth: bool = True,
    ) -> Dict[str, Any]:
        response = await self._client.post(
            f"{self.STRIPE_PREFIX}{path}",
            json=json,
            headers=self._build_headers(access_token_override, require_auth=require_auth),
        )
        return await self._parse_response(response)

    def _build_headers(
        self,
        access_token_override: Optional[str],
        *,
        require_auth: bool = True,
    ) -> Dict[str, str]:
        headers: Dict[str, str] = {"X-API-Key": self.api_key}
        if require_auth:
            token = access_token_override or self.access_token
            if not token:
                raise ValueError("Access token is required for payment operations")
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def _parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        if response.status_code >= 400:
            raise await self._build_error(response)
        payload = response.json()
        return payload.get("data", payload)

    @staticmethod
    async def _build_error(response: httpx.Response) -> PaymentsError:
        try:
            payload = response.json()
        except ValueError:  # pragma: no cover
            payload = {}
        error_info = payload.get("error", {})
        message = error_info.get("message") or response.text or "Payments request failed"
        request_id = (
            response.headers.get("x-request-id")
            or payload.get("metadata", {}).get("request_id")
        )
        return PaymentsError(
            message,
            status_code=response.status_code,
            error_code=error_info.get("code"),
            response=response,
            request_id=request_id,
        )


__all__ = ["AsyncPaymentsClient"]
