"""
Payments helpers for the Sweet Potato Authentication & Payment Service.

This module wraps payment-related endpoints including Stripe checkout sessions
and balance tracking.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel, ConfigDict, Field

from .crypto import CryptoPaymentsClient

__all__ = [
    "PaymentsClient",
    "PaymentsError",
    "CheckoutSession",
    "CheckoutSessionDetails",
    "CheckoutSessionSummary",
    "CheckoutSessionList",
    "ExpireCheckoutSessionResult",
    "PaymentIntent",
    "WalletDeposit",
    "WalletTransaction",
    "SubscriptionPlan",
    "SubscriptionItemPriceRecurring",
    "SubscriptionItemPrice",
    "SubscriptionItem",
    "SubscriptionDetail",
    "SubscriptionCancellation",
    "SubscriptionList",
    "BalanceAmounts",
    "UsageSummary",
    "BalanceOverview",
    "PaymentMethodUpdateResult",
    "ProductPrice",
    "Product",
    "ProductList",
    "GuestCheckoutSession",
    "GuestCheckoutSessionSummary",
    "GuestCheckoutSessionList",
    "GuestCheckoutConversionResult",
    "PaymentRecord",
    "PaymentHistory",
]


class PaymentsError(Exception):
    """Raised when a payments endpoint returns an error response."""

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


class CheckoutSession(BaseModel):
    """Stripe checkout session metadata."""

    model_config = ConfigDict(extra="ignore")

    session_id: str
    checkout_url: str
    expires_at: Optional[dt.datetime] = None


class PaymentIntent(BaseModel):
    """Stripe payment intent response."""

    model_config = ConfigDict(extra="ignore")

    payment_intent_id: str
    client_secret: Optional[str] = None
    status: Optional[str] = None


class WalletDeposit(BaseModel):
    """Wallet deposit submission status."""

    model_config = ConfigDict(extra="ignore")

    deposit_id: str
    status: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    confirmation_required: Optional[int] = None
    confirmation_current: Optional[int] = None


class WalletTransaction(BaseModel):
    """Wallet transaction confirmation status."""

    model_config = ConfigDict(extra="ignore")

    transaction_id: str
    status: Optional[str] = None
    confirmations: Optional[int] = None
    chain_type: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    balance_added: Optional[float] = None
    completed_at: Optional[dt.datetime] = None


class SubscriptionPlan(BaseModel):
    """Condensed view of the active price/plan."""

    model_config = ConfigDict(extra="ignore")

    price_id: Optional[str] = None
    product_id: Optional[str] = None
    unit_amount: Optional[int] = None
    currency: Optional[str] = None
    interval: Optional[str] = None
    interval_count: Optional[int] = None


class SubscriptionItemPriceRecurring(BaseModel):
    """Recurring billing metadata for a Stripe price."""

    model_config = ConfigDict(extra="ignore")

    interval: Optional[str] = None
    interval_count: Optional[int] = None


class SubscriptionItemPrice(BaseModel):
    """Stripe price attached to a subscription item."""

    model_config = ConfigDict(extra="ignore")

    id: str
    product: Optional[str] = None
    unit_amount: Optional[int] = None
    currency: Optional[str] = None
    recurring: Optional[SubscriptionItemPriceRecurring] = None


class SubscriptionItem(BaseModel):
    """Subscription line item."""

    model_config = ConfigDict(extra="ignore")

    id: str
    price: SubscriptionItemPrice


class SubscriptionDetail(BaseModel):
    """Active subscription information."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str = Field(alias="id")
    subscription_id: Optional[str] = Field(default=None, alias="subscription_id")
    status: Optional[str] = None
    current_period_start: Optional[int] = None
    current_period_end: Optional[int] = None
    cancel_at_period_end: Optional[bool] = None
    canceled_at: Optional[int] = None
    items: list[SubscriptionItem] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if self.subscription_id and not self.id:
            object.__setattr__(self, "id", self.subscription_id)
        elif self.id and not self.subscription_id:
            object.__setattr__(self, "subscription_id", self.id)

    @property
    def plan(self) -> Optional[SubscriptionPlan]:
        """Backwards compatible view of the primary subscription plan."""

        if not self.items:
            return None
        price = self.items[0].price
        recurring = price.recurring or SubscriptionItemPriceRecurring()
        return SubscriptionPlan(
            price_id=price.id,
            product_id=price.product,
            unit_amount=price.unit_amount,
            currency=price.currency,
            interval=recurring.interval,
            interval_count=recurring.interval_count,
        )


class SubscriptionCancellation(BaseModel):
    """Cancellation request result."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(alias="id")
    status: Optional[str] = None
    cancel_at_period_end: Optional[bool] = None
    canceled_at: Optional[int] = None
    items: list[SubscriptionItem] = Field(default_factory=list)

    @property
    def subscription_id(self) -> str:
        return self.id


class SubscriptionList(BaseModel):
    """Wrapper for subscription listings."""

    model_config = ConfigDict(extra="ignore")

    subscriptions: list[SubscriptionDetail] = Field(default_factory=list)
    has_more: bool = False


class CheckoutSessionDetails(BaseModel):
    """Detailed representation of a Stripe checkout session."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    status: Optional[str] = None
    payment_status: Optional[str] = None
    customer_email: Optional[str] = Field(default=None, alias="customer_email")
    amount_total: Optional[int] = None
    currency: Optional[str] = None
    success_url: Optional[str] = Field(default=None, alias="success_url")
    cancel_url: Optional[str] = Field(default=None, alias="cancel_url")
    client_reference_id: Optional[str] = Field(default=None, alias="client_reference_id")
    metadata: Optional[Dict[str, Any]] = None
    payment_intent: Optional[str] = None
    subscription: Optional[str] = None
    expires_at: Optional[int] = None


class CheckoutSessionSummary(BaseModel):
    """Summary view for checkout session listings."""

    model_config = ConfigDict(extra="ignore")

    id: str
    status: Optional[str] = None
    payment_status: Optional[str] = None
    amount_total: Optional[int] = None
    currency: Optional[str] = None
    created_at: Optional[int] = None
    expires_at: Optional[int] = None


class CheckoutSessionList(BaseModel):
    """Listing response for checkout sessions."""

    model_config = ConfigDict(extra="ignore")

    sessions: list[CheckoutSessionSummary] = Field(default_factory=list)
    has_more: bool = False
    next_cursor: Optional[str] = None


class ExpireCheckoutSessionResult(BaseModel):
    """Response returned after expiring a checkout session."""

    model_config = ConfigDict(extra="ignore")

    id: str
    status: Optional[str] = None
    expired: bool = False


class GuestCheckoutSession(BaseModel):
    """Created guest checkout session metadata."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    url: Optional[str] = None
    expires_at: Optional[int] = Field(default=None, alias="expiresAt")
    customer_email: Optional[str] = Field(default=None, alias="customerEmail")
    client_reference_id: Optional[str] = Field(default=None, alias="clientReferenceId")
    success_url: Optional[str] = Field(default=None, alias="successUrl")
    cancel_url: Optional[str] = Field(default=None, alias="cancelUrl")


class GuestCheckoutSessionSummary(BaseModel):
    """Summary of guest checkout sessions from database listings."""

    model_config = ConfigDict(extra="ignore")

    session_id: str
    status: Optional[str] = None
    payment_status: Optional[str] = None
    customer_email: Optional[str] = None
    amount_total: Optional[int] = None
    currency: Optional[str] = None
    created_at: Optional[str] = None
    expires_at: Optional[str] = None


class GuestCheckoutSessionList(BaseModel):
    """Guest checkout session listing wrapper."""

    model_config = ConfigDict(extra="ignore")

    sessions: list[GuestCheckoutSessionSummary] = Field(default_factory=list)
    has_more: bool = False


class GuestCheckoutConversionResult(BaseModel):
    """Result of converting a guest checkout into a user account."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    success: bool
    user_id: Optional[str] = Field(default=None, alias="userId")
    message: Optional[str] = None
    login_url: Optional[str] = Field(default=None, alias="loginUrl")
    magic_link_sent: Optional[bool] = Field(default=None, alias="magicLinkSent")


class PaymentRecord(BaseModel):
    """Stripe or wallet payment entry."""

    model_config = ConfigDict(extra="ignore")

    id: str
    amount: Optional[int] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    created: Optional[int] = None
    payment_method_type: Optional[str] = None
    invoice_id: Optional[str] = None
    invoice_pdf: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PaymentHistory(BaseModel):
    """Composite payment history listing."""

    model_config = ConfigDict(extra="ignore")

    payments: list[PaymentRecord] = Field(default_factory=list)
    has_more: bool = False
    total_count: Optional[int] = None


class BalanceAmounts(BaseModel):
    """Breakdown of available/pending balances."""

    model_config = ConfigDict(extra="ignore")

    available: float
    pending: float
    currency: str


class UsageSummary(BaseModel):
    """Usage metrics for the current billing period."""

    model_config = ConfigDict(extra="ignore")

    current_period_start: Optional[dt.datetime] = None
    current_period_end: Optional[dt.datetime] = None
    credits_used: Optional[int] = None
    credits_remaining: Optional[int] = None


class BalanceOverview(BaseModel):
    """Composite balance information."""

    model_config = ConfigDict(extra="ignore")

    balance: BalanceAmounts
    tier: Optional[str] = None
    tier_expires_at: Optional[dt.datetime] = None
    usage: UsageSummary


class PaymentMethodUpdateResult(BaseModel):
    """Result of updating the default payment method."""

    model_config = ConfigDict(extra="ignore")

    message: Optional[str] = None
    customer_id: Optional[str] = None
    payment_method_id: str
    is_default: bool = False


class ProductPrice(BaseModel):
    """Price information associated with a product."""

    model_config = ConfigDict(extra="ignore")

    id: str
    unit_amount: Optional[int] = None
    currency: Optional[str] = None
    type: Optional[str] = None
    recurring: Optional[Dict[str, Any]] = None
    nickname: Optional[str] = None
    active: Optional[bool] = None


class Product(BaseModel):
    """Stripe product with optional pricing metadata."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    description: Optional[str] = None
    images: Optional[list[str]] = None
    active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    prices: list[ProductPrice] = Field(default_factory=list)
    default_price: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


class ProductList(BaseModel):
    """Collection wrapper for product listings."""

    model_config = ConfigDict(extra="ignore")

    products: list[Product] = Field(default_factory=list)
    total: int
    admin_metadata: Optional[Dict[str, Any]] = Field(default=None, alias="adminMetadata")


class PaymentsClient:
    """Client wrapper for payment endpoints."""

    PAYMENTS_PREFIX = "/api/payments"
    STRIPE_PREFIX = "/api/stripe"

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
        self.crypto: CryptoPaymentsClient = CryptoPaymentsClient(
            client=self._client,
            header_builder=self._build_headers,
        )

    def __enter__(self) -> "PaymentsClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore[override]
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    # Public API

    def create_checkout_session(
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

        data = self._post(
            "/create-checkout-session",
            json=payload,
            access_token_override=access_token_override,
        )
        return CheckoutSession.model_validate(data)

    def get_balance(
        self,
        *,
        access_token_override: Optional[str] = None,
    ) -> BalanceOverview:
        data = self._get("/balance", access_token_override=access_token_override)
        return BalanceOverview.model_validate(data)

    def create_payment_intent(
        self,
        *,
        amount: int,
        currency: str,
        payment_method_types: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        access_token_override: Optional[str] = None,
    ) -> PaymentIntent:
        payload: Dict[str, Any] = {
            "amount": amount,
            "currency": currency,
        }
        if payment_method_types is not None:
            payload["payment_method_types"] = payment_method_types
        if metadata:
            payload["metadata"] = metadata

        data = self._post(
            "/create-payment-intent",
            json=payload,
            access_token_override=access_token_override,
        )
        return PaymentIntent.model_validate(data)

    def update_payment_method(
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
        data = self._post(
            "/update-payment-method",
            json=payload,
            access_token_override=access_token_override,
        )
        return PaymentMethodUpdateResult.model_validate(data)

    def wallet_deposit(
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

        data = self._post(
            "/wallet-deposit",
            json=payload,
            access_token_override=access_token_override,
        )
        return WalletDeposit.model_validate(data)

    def get_wallet_transaction(
        self,
        *,
        transaction_id: str,
        access_token_override: Optional[str] = None,
    ) -> WalletTransaction:
        data = self._get(
            f"/wallet-transaction/{transaction_id}",
            access_token_override=access_token_override,
        )
        return WalletTransaction.model_validate(data)

    def get_subscription(
        self,
        *,
        subscription_id: str,
        access_token_override: Optional[str] = None,
    ) -> SubscriptionDetail:
        data = self._get_stripe(
            f"/subscription/{subscription_id}",
            params=None,
            access_token_override=access_token_override,
        )
        return SubscriptionDetail.model_validate(data)

    def list_subscriptions(
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

        data = self._get_stripe(
            "/subscriptions",
            params=params or None,
            access_token_override=access_token_override,
        )
        return SubscriptionList.model_validate(data)

    def cancel_subscription(
        self,
        *,
        subscription_id: str,
        immediately: Optional[bool] = None,
        access_token_override: Optional[str] = None,
    ) -> SubscriptionCancellation:
        payload: Dict[str, Any] = {}
        if immediately is not None:
            payload["immediately"] = immediately

        data = self._post_stripe(
            f"/subscription/{subscription_id}/cancel",
            json=payload,
            access_token_override=access_token_override,
        )
        return SubscriptionCancellation.model_validate(data)

    def update_subscription(
        self,
        *,
        subscription_id: str,
        price_id: str,
        access_token_override: Optional[str] = None,
    ) -> SubscriptionDetail:
        if not price_id:
            raise ValueError("price_id is required")

        data = self._post_stripe(
            f"/subscription/{subscription_id}/update",
            json={"price_id": price_id},
            access_token_override=access_token_override,
        )
        return SubscriptionDetail.model_validate(data)

    def get_checkout_session(
        self,
        *,
        session_id: str,
        access_token_override: Optional[str] = None,
    ) -> CheckoutSessionDetails:
        data = self._get_stripe(
            f"/checkout-sessions/{session_id}",
            params=None,
            access_token_override=access_token_override,
        )
        return CheckoutSessionDetails.model_validate(data)

    def list_checkout_sessions(
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

        data = self._get_stripe(
            "/checkout-sessions",
            params=params or None,
            access_token_override=access_token_override,
        )
        return CheckoutSessionList.model_validate(data)

    def expire_checkout_session(
        self,
        *,
        session_id: str,
        access_token_override: Optional[str] = None,
    ) -> ExpireCheckoutSessionResult:
        data = self._post_stripe(
            f"/checkout-sessions/{session_id}/expire",
            json={},
            access_token_override=access_token_override,
        )
        return ExpireCheckoutSessionResult.model_validate(data)

    def create_guest_checkout_session(
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

        data = self._post_stripe(
            "/guest-checkout-sessions",
            json=payload,
            access_token_override=None,
            require_auth=False,
        )
        return GuestCheckoutSession.model_validate(data)

    def get_guest_checkout_session(
        self,
        *,
        session_id: str,
    ) -> CheckoutSessionDetails:
        data = self._get_stripe(
            f"/guest-checkout-sessions/{session_id}",
            params=None,
            access_token_override=None,
            require_auth=False,
        )
        return CheckoutSessionDetails.model_validate(data)

    def list_guest_checkout_sessions(
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

        data = self._get_stripe(
            "/guest-checkout-sessions",
            params=params or None,
            access_token_override=None,
            require_auth=False,
        )
        return GuestCheckoutSessionList.model_validate(data)

    def convert_guest_checkout_session(
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

        data = self._post_stripe(
            "/guest-checkout-sessions/convert",
            json=payload,
            access_token_override=None,
            require_auth=False,
        )
        return GuestCheckoutConversionResult.model_validate(data)

    def list_payment_history(
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

        data = self._get_stripe(
            "/history",
            params=params or None,
            access_token_override=access_token_override,
        )
        return PaymentHistory.model_validate(data)

    def get_payment_detail(
        self,
        *,
        payment_id: str,
        access_token_override: Optional[str] = None,
    ) -> PaymentRecord:
        data = self._get_stripe(
            f"/payment/{payment_id}",
            params=None,
            access_token_override=access_token_override,
        )
        if isinstance(data, dict) and "payment" in data:
            return PaymentRecord.model_validate(data["payment"])
        return PaymentRecord.model_validate(data)

    def list_products(
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

        data = self._get_stripe(
            "/products",
            params=params or None,
            access_token_override=access_token_override,
        )
        return ProductList.model_validate(data)

    def get_product(
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

        data = self._get_stripe(
            f"/products/{product_id}",
            params=params,
            access_token_override=access_token_override,
        )
        return Product.model_validate(data)

    # Internal helpers

    def _get(self, path: str, *, access_token_override: Optional[str]) -> Dict[str, Any]:
        response = self._client.get(
            f"{self.PAYMENTS_PREFIX}{path}",
            headers=self._build_headers(access_token_override),
        )
        return self._parse_response(response)

    def _get_stripe(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]],
        access_token_override: Optional[str],
        require_auth: bool = True,
    ) -> Dict[str, Any]:
        response = self._client.get(
            f"{self.STRIPE_PREFIX}{path}",
            params=params,
            headers=self._build_headers(access_token_override, require_auth=require_auth),
        )
        return self._parse_response(response)

    def _post(self, path: str, *, json: Dict[str, Any], access_token_override: Optional[str]) -> Dict[str, Any]:
        response = self._client.post(
            f"{self.PAYMENTS_PREFIX}{path}",
            json=json,
            headers=self._build_headers(access_token_override),
        )
        return self._parse_response(response)

    def _post_stripe(
        self,
        path: str,
        *,
        json: Dict[str, Any],
        access_token_override: Optional[str],
        require_auth: bool = True,
    ) -> Dict[str, Any]:
        response = self._client.post(
            f"{self.STRIPE_PREFIX}{path}",
            json=json,
            headers=self._build_headers(access_token_override, require_auth=require_auth),
        )
        return self._parse_response(response)

    def _build_headers(
        self,
        access_token_override: Optional[str],
        *,
        require_auth: bool = True,
    ) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "X-API-Key": self.api_key,
        }
        if require_auth:
            token = access_token_override or self.access_token
            if not token:
                raise ValueError("Access token is required for payment operations")
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _parse_response(self, response: httpx.Response) -> Dict[str, Any]:
        if response.status_code >= 400:
            raise self._build_error(response)
        payload = response.json()
        return payload.get("data", payload)

    @staticmethod
    def _build_error(response: httpx.Response) -> PaymentsError:
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
