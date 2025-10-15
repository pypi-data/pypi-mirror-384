import json
from typing import Any, Dict

import pytest
import respx
from httpx import Response

from spaps_client import payments
from spaps_client.crypto import verify_crypto_webhook_signature


@pytest.fixture()
def base_url() -> str:
    return "https://api.sweetpotato.dev"


@pytest.fixture()
def api_key() -> str:
    return "test_key_local_dev_only"


@pytest.fixture()
def access_token() -> str:
    return "access-token"


@pytest.fixture()
def payments_client(base_url: str, api_key: str, access_token: str) -> payments.PaymentsClient:
    return payments.PaymentsClient(base_url=base_url, api_key=api_key, access_token=access_token)


@pytest.fixture()
def checkout_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "session_id": "cs_test_abc123",
            "checkout_url": "https://checkout.stripe.com/pay/cs_test_abc123",
            "expires_at": "2025-01-09T11:30:00Z",
        },
    }


@pytest.fixture()
def balance_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "balance": {
                "available": 250.0,
                "pending": 100.0,
                "currency": "USD",
            },
            "tier": "premium",
            "tier_expires_at": "2025-02-09T00:00:00Z",
            "usage": {
                "current_period_start": "2025-01-01T00:00:00Z",
                "current_period_end": "2025-01-31T23:59:59Z",
                "credits_used": 150,
                "credits_remaining": 850,
            },
        },
    }


@respx.mock
def test_create_checkout_session_success(payments_client: payments.PaymentsClient, base_url: str, api_key: str, access_token: str, checkout_payload: Dict[str, Any]) -> None:
    route = respx.post(f"{base_url}/api/payments/create-checkout-session").mock(return_value=Response(200, json=checkout_payload))

    result = payments_client.create_checkout_session(
        price_id="price_1234567890",
        mode="subscription",
        success_url="https://yourapp.com/success",
        cancel_url="https://yourapp.com/cancel",
        metadata={"user_id": "user_123"},
    )

    assert route.called, "Checkout session endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    body = json.loads(request.content.decode())
    assert body == {
        "price_id": "price_1234567890",
        "mode": "subscription",
        "success_url": "https://yourapp.com/success",
        "cancel_url": "https://yourapp.com/cancel",
        "metadata": {"user_id": "user_123"},
    }

    assert result.session_id == checkout_payload["data"]["session_id"]
    assert result.checkout_url == checkout_payload["data"]["checkout_url"]


@respx.mock
def test_create_checkout_session_error(payments_client: payments.PaymentsClient, base_url: str) -> None:
    respx.post(f"{base_url}/api/payments/create-checkout-session").mock(
        return_value=Response(400, json={"success": False, "error": {"code": "INVALID_PRICE", "message": "Price not found"}}),
    )

    with pytest.raises(payments.PaymentsError) as exc:
        payments_client.create_checkout_session(
            price_id="price_missing",
            mode="subscription",
            success_url="https://yourapp.com/success",
            cancel_url="https://yourapp.com/cancel",
        )

    assert exc.value.status_code == 400
    assert exc.value.error_code == "INVALID_PRICE"


@respx.mock
def test_get_balance_success(payments_client: payments.PaymentsClient, base_url: str, api_key: str, access_token: str, balance_payload: Dict[str, Any]) -> None:
    route = respx.get(f"{base_url}/api/payments/balance").mock(return_value=Response(200, json=balance_payload))

    result = payments_client.get_balance()

    assert route.called, "Balance endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"

    assert result.balance.available == 250.0
    assert result.balance.currency == "USD"
    assert result.usage.credits_remaining == 850


@respx.mock
def test_get_balance_error(payments_client: payments.PaymentsClient, base_url: str) -> None:
    respx.get(f"{base_url}/api/payments/balance").mock(
        return_value=Response(401, json={"success": False, "error": {"code": "UNAUTHORIZED", "message": "Missing token"}}),
    )

    with pytest.raises(payments.PaymentsError) as exc:
        payments_client.get_balance()

    assert exc.value.status_code == 401
    assert exc.value.error_code == "UNAUTHORIZED"


@pytest.fixture()
def payment_intent_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "payment_intent_id": "pi_12345",
            "client_secret": "pi_12345_secret_67890",
            "status": "requires_confirmation",
        },
    }


@pytest.fixture()
def wallet_deposit_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "deposit_id": "dep_abc123",
            "status": "pending",
            "amount": 100.0,
            "currency": "USDC",
            "confirmation_required": 12,
            "confirmation_current": 0,
        },
    }


@pytest.fixture()
def transaction_status_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "transaction_id": "0x123abc",
            "status": "confirmed",
            "confirmations": 12,
            "chain_type": "ethereum",
            "amount": 100.0,
            "currency": "USDC",
            "balance_added": 100.0,
            "completed_at": "2025-01-09T10:45:00Z",
        },
    }


@pytest.fixture()
def subscription_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "id": "sub_1234567890",
            "status": "active",
            "current_period_start": 1_700_000_000,
            "current_period_end": 1_702_592_000,
            "cancel_at_period_end": False,
            "canceled_at": None,
            "items": [
                {
                    "id": "si_123",
                    "price": {
                        "id": "price_basic",
                        "product": "prod_basic",
                        "unit_amount": 2_000,
                        "currency": "usd",
                        "recurring": {
                            "interval": "month",
                            "interval_count": 1,
                        },
                    },
                },
            ],
        },
    }


@pytest.fixture()
def subscription_list_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "subscriptions": [
                {
                    "id": "sub_1234567890",
                    "status": "active",
                    "current_period_start": 1_700_000_000,
                    "current_period_end": 1_702_592_000,
                    "cancel_at_period_end": False,
                    "canceled_at": None,
                    "items": [
                        {
                            "id": "si_123",
                            "price": {
                                "id": "price_basic",
                                "product": "prod_basic",
                                "unit_amount": 2_000,
                                "currency": "usd",
                                "recurring": {
                                    "interval": "month",
                                    "interval_count": 1,
                                },
                            },
                        }
                    ],
                }
            ],
            "has_more": False,
        },
    }


@pytest.fixture()
def cancel_subscription_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "id": "sub_1234567890",
            "status": "canceled",
            "current_period_start": 1_700_000_000,
            "current_period_end": 1_702_592_000,
            "cancel_at_period_end": True,
            "canceled_at": 1_700_500_000,
            "items": [
                {
                    "id": "si_123",
                    "price": {
                        "id": "price_basic",
                        "product": "prod_basic",
                        "unit_amount": 2_000,
                        "currency": "usd",
                        "recurring": {
                            "interval": "month",
                            "interval_count": 1,
                        },
                    },
                },
            ],
        },
    }


@pytest.fixture()
def checkout_session_detail_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "id": "cs_test_123",
            "status": "complete",
            "payment_status": "paid",
            "customer_email": "user@example.com",
            "amount_total": 4_200,
            "currency": "usd",
            "success_url": "https://app.example.com/success",
            "cancel_url": "https://app.example.com/cancel",
            "client_reference_id": "order_123",
            "metadata": {"app_id": "app_123"},
            "payment_intent": "pi_123",
            "subscription": "sub_1234567890",
            "expires_at": 1_700_100_000,
        },
    }


@pytest.fixture()
def checkout_sessions_list_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "sessions": [
                {
                    "id": "cs_test_123",
                    "status": "open",
                    "payment_status": "unpaid",
                    "amount_total": 2_000,
                    "currency": "usd",
                    "created_at": 1_700_000_500,
                    "expires_at": 1_700_001_000,
                }
            ],
            "has_more": False,
            "next_cursor": None,
        },
    }


@pytest.fixture()
def expire_checkout_session_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "id": "cs_test_123",
            "status": "expired",
            "expired": True,
        },
    }


@pytest.fixture()
def guest_checkout_create_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "id": "cs_test_guest",
            "url": "https://checkout.stripe.com/pay/cs_test_guest",
            "expiresAt": 1_700_001_800,
            "customerEmail": "guest@example.com",
            "clientReferenceId": "guest_ref_123",
            "successUrl": "https://app.example.com/success",
            "cancelUrl": "https://app.example.com/cancel",
        },
    }


@pytest.fixture()
def guest_checkout_detail_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "id": "cs_test_guest",
            "status": "complete",
            "payment_status": "paid",
            "customer_email": "guest@example.com",
            "amount_total": 5_000,
            "currency": "usd",
            "success_url": "https://app.example.com/success",
            "cancel_url": "https://app.example.com/cancel",
            "client_reference_id": "guest_ref_123",
            "metadata": {"app_id": "app_123", "is_guest": "true"},
            "payment_intent": "pi_guest_123",
            "subscription": None,
            "expires_at": 1_700_002_000,
        },
    }


@pytest.fixture()
def guest_checkout_list_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "sessions": [
                {
                    "session_id": "cs_test_guest",
                    "status": "open",
                    "payment_status": "unpaid",
                    "customer_email": "guest@example.com",
                    "amount_total": 4_200,
                    "currency": "usd",
                    "created_at": "2025-01-01T00:00:00Z",
                    "expires_at": "2025-01-01T00:30:00Z",
                }
            ],
            "has_more": False,
        },
    }


@pytest.fixture()
def guest_checkout_convert_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "success": True,
            "userId": "user_123",
            "message": "Checkout linked to existing account",
            "magicLinkSent": True,
        },
    }


@pytest.fixture()
def payment_history_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "payments": [
                {
                    "id": "pi_123",
                    "amount": 4_200,
                    "currency": "usd",
                    "status": "succeeded",
                    "description": "Monthly subscription",
                    "created": 1_700_000_800,
                    "payment_method_type": "card",
                    "invoice_id": "in_123",
                    "invoice_pdf": "https://stripe.com/invoices/in_123.pdf",
                    "metadata": {"app_id": "app_123"},
                }
            ],
            "has_more": False,
            "total_count": 1,
        },
    }


@pytest.fixture()
def payment_detail_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "payment": {
                "id": "pi_123",
                "amount": 4_200,
                "currency": "usd",
                "status": "succeeded",
                "description": "Monthly subscription",
                "created": 1_700_000_800,
                "payment_method_type": "card",
                "invoice_id": "in_123",
                "invoice_pdf": "https://stripe.com/invoices/in_123.pdf",
                "metadata": {"app_id": "app_123"},
            }
        },
    }


@pytest.fixture()
def update_payment_method_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "message": "Default payment method updated",
            "customer_id": "cus_123",
            "payment_method_id": "pm_abc123",
            "is_default": True,
        },
    }


@pytest.fixture()
def crypto_invoice_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "invoice": {
                "invoice_id": "inv_01J1CJZ3H6TQ1FA6HJX2Y5M3VE",
                "asset": "USDC",
                "network": "base",
                "amount": "42.75",
                "status": "pending",
                "expires_at": "2025-01-09T10:45:00Z",
                "metadata": {
                    "order_id": "ord_123",
                    "application_id": "app_789"
                },
            }
        },
    }


@pytest.fixture()
def crypto_invoice_status_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "invoice_id": "inv_01J1CJZ3H6TQ1FA6HJX2Y5M3VE",
            "status": "confirmed",
            "finalized_at": "2025-01-09T11:00:00Z",
            "normalized_amount": "42.75",
            "settlement_ids": ["ledg_01J1CK5K3QPKM783X2TSZGSQEG"],
        },
    }


@pytest.fixture()
def crypto_reconcile_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "job_id": "job_123",
            "scheduled_at": "2025-01-09T11:05:00Z",
            "cursor": {
                "last_invoice_id": "inv_01J1CJZ3H6TQ1FA6HJX2Y5M3VE"
            },
        },
    }


@pytest.fixture()
def products_list_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "products": [
                {
                    "id": "prod_123",
                    "name": "Sweet Potato Pro",
                    "description": "Premium tier",
                    "active": True,
                    "metadata": {"app_id": "app_123"},
                    "prices": [
                        {
                            "id": "price_monthly",
                            "unit_amount": 2000,
                            "currency": "usd",
                            "type": "recurring",
                            "recurring": {"interval": "month", "interval_count": 1},
                            "nickname": "Monthly",
                            "active": True,
                        }
                    ],
                    "default_price": {
                        "id": "price_monthly",
                        "unit_amount": 2000,
                        "currency": "usd",
                    },
                    "created_at": "2025-01-01T00:00:00Z",
                }
            ],
            "total": 1,
        },
    }


@pytest.fixture()
def product_detail_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "id": "prod_123",
            "name": "Sweet Potato Pro",
            "description": "Premium tier",
            "images": ["https://cdn.example.com/pro.png"],
            "active": True,
            "metadata": {"app_id": "app_123"},
            "prices": [
                {
                    "id": "price_monthly",
                    "unit_amount": 2000,
                    "currency": "usd",
                    "type": "recurring",
                    "recurring": {"interval": "month", "interval_count": 1},
                    "nickname": "Monthly",
                    "active": True,
                }
            ],
            "created_at": "2025-01-01T00:00:00Z",
        },
    }


@respx.mock
def test_create_payment_intent_success(payments_client: payments.PaymentsClient, base_url: str, api_key: str, access_token: str, payment_intent_payload: Dict[str, Any]) -> None:
    route = respx.post(f"{base_url}/api/payments/create-payment-intent").mock(return_value=Response(200, json=payment_intent_payload))

    result = payments_client.create_payment_intent(
        amount=5000,
        currency="usd",
        payment_method_types=["card"],
        metadata={"order_id": "order_123"},
    )

    assert route.called, "Create payment intent endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    body = json.loads(request.content.decode())
    assert body == {
        "amount": 5000,
        "currency": "usd",
        "payment_method_types": ["card"],
        "metadata": {"order_id": "order_123"},
    }

    assert result.payment_intent_id == "pi_12345"
    assert result.status == "requires_confirmation"


@respx.mock
def test_create_payment_intent_error(payments_client: payments.PaymentsClient, base_url: str) -> None:
    respx.post(f"{base_url}/api/payments/create-payment-intent").mock(
        return_value=Response(402, json={"success": False, "error": {"code": "CARD_DECLINED", "message": "Card declined"}}),
    )

    with pytest.raises(payments.PaymentsError) as exc:
        payments_client.create_payment_intent(amount=5000, currency="usd", payment_method_types=["card"])

    assert exc.value.status_code == 402
    assert exc.value.error_code == "CARD_DECLINED"


@respx.mock
def test_wallet_deposit_success(payments_client: payments.PaymentsClient, base_url: str, api_key: str, access_token: str, wallet_deposit_payload: Dict[str, Any]) -> None:
    route = respx.post(f"{base_url}/api/payments/wallet-deposit").mock(return_value=Response(200, json=wallet_deposit_payload))

    result = payments_client.wallet_deposit(
        wallet_address="0x742d35Cc6637C0532925a3b844Bc454e2b3edb19",
        chain_type="ethereum",
        transaction_id="0x123abc",
        amount=100.0,
        currency="USDC",
        tier="premium",
    )

    assert route.called, "Wallet deposit endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    body = json.loads(request.content.decode())
    assert body == {
        "wallet_address": "0x742d35Cc6637C0532925a3b844Bc454e2b3edb19",
        "chain_type": "ethereum",
        "transaction_id": "0x123abc",
        "amount": 100.0,
        "currency": "USDC",
        "tier": "premium",
    }

    assert result.deposit_id == "dep_abc123"
    assert result.status == "pending"


@respx.mock
def test_wallet_deposit_error(payments_client: payments.PaymentsClient, base_url: str) -> None:
    respx.post(f"{base_url}/api/payments/wallet-deposit").mock(
        return_value=Response(422, json={"success": False, "error": {"code": "INVALID_TRANSACTION", "message": "Transaction already processed"}}),
    )

    with pytest.raises(payments.PaymentsError) as exc:
        payments_client.wallet_deposit(
            wallet_address="0x742d35Cc6637C0532925a3b844Bc454e2b3edb19",
            chain_type="ethereum",
            transaction_id="0x123abc",
            amount=100.0,
            currency="USDC",
        )

    assert exc.value.status_code == 422
    assert exc.value.error_code == "INVALID_TRANSACTION"


@respx.mock
def test_update_payment_method_success(
    payments_client: payments.PaymentsClient,
    base_url: str,
    api_key: str,
    access_token: str,
    update_payment_method_payload: Dict[str, Any],
) -> None:
    route = respx.post(f"{base_url}/api/payments/update-payment-method").mock(
        return_value=Response(200, json=update_payment_method_payload)
    )

    result = payments_client.update_payment_method(payment_method_id="pm_abc123", set_default=True)

    assert route.called, "Update payment method endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    body = json.loads(request.content.decode())
    assert body == {"payment_method_id": "pm_abc123", "set_default": True}

    assert result.payment_method_id == "pm_abc123"
    assert result.is_default is True
    assert "updated" in result.message


@respx.mock
def test_update_payment_method_error(payments_client: payments.PaymentsClient, base_url: str) -> None:
    respx.post(f"{base_url}/api/payments/update-payment-method").mock(
        return_value=Response(404, json={"success": False, "error": {"code": "PAYMENT_METHOD_NOT_FOUND", "message": "Payment method not found"}}),
    )

    with pytest.raises(payments.PaymentsError) as exc:
        payments_client.update_payment_method(payment_method_id="pm_missing")

    assert exc.value.status_code == 404
    assert exc.value.error_code == "PAYMENT_METHOD_NOT_FOUND"


@respx.mock
def test_crypto_create_invoice_success(
    payments_client: payments.PaymentsClient,
    base_url: str,
    api_key: str,
    access_token: str,
    crypto_invoice_payload: Dict[str, Any],
) -> None:
    route = respx.post(f"{base_url}/api/payments/crypto/invoices").mock(return_value=Response(200, json=crypto_invoice_payload))

    invoice = payments_client.crypto.create_invoice(
        asset="USDC",
        network="base",
        amount="42.75",
        expires_in_seconds=900,
        metadata={"order_id": "ord_123"},
    )

    assert route.called, "Create crypto invoice endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    body = json.loads(request.content.decode())
    assert body["asset"] == "USDC"
    assert body["network"] == "base"
    assert body["amount"] == "42.75"
    assert body["expires_in_seconds"] == 900
    assert body["metadata"] == {"order_id": "ord_123"}

    assert invoice.invoice_id == "inv_01J1CJZ3H6TQ1FA6HJX2Y5M3VE"
    assert invoice.status == "pending"


@respx.mock
def test_crypto_get_invoice_success(
    payments_client: payments.PaymentsClient,
    base_url: str,
    crypto_invoice_payload: Dict[str, Any],
) -> None:
    respx.get(f"{base_url}/api/payments/crypto/invoices/inv_01J1CJZ3H6TQ1FA6HJX2Y5M3VE").mock(return_value=Response(200, json=crypto_invoice_payload))

    invoice = payments_client.crypto.get_invoice("inv_01J1CJZ3H6TQ1FA6HJX2Y5M3VE")

    assert invoice.invoice_id == "inv_01J1CJZ3H6TQ1FA6HJX2Y5M3VE"
    assert invoice.amount == "42.75"


@respx.mock
def test_crypto_get_invoice_status(
    payments_client: payments.PaymentsClient,
    base_url: str,
    crypto_invoice_status_payload: Dict[str, Any],
) -> None:
    respx.get(f"{base_url}/api/payments/crypto/invoices/inv_01J1CJZ3H6TQ1FA6HJX2Y5M3VE/status").mock(return_value=Response(200, json=crypto_invoice_status_payload))

    status = payments_client.crypto.get_invoice_status("inv_01J1CJZ3H6TQ1FA6HJX2Y5M3VE")

    assert status.invoice_id == "inv_01J1CJZ3H6TQ1FA6HJX2Y5M3VE"
    assert status.status == "confirmed"
    assert status.normalized_amount == "42.75"


@respx.mock
def test_crypto_reconcile(
    payments_client: payments.PaymentsClient,
    base_url: str,
    api_key: str,
    access_token: str,
    crypto_reconcile_payload: Dict[str, Any],
) -> None:
    route = respx.post(f"{base_url}/api/payments/crypto/reconcile").mock(return_value=Response(200, json=crypto_reconcile_payload))

    job = payments_client.crypto.reconcile(recon_token="recon_123", cursor={"last_invoice_id": "inv_123"})

    assert route.called, "Crypto reconcile endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    assert request.headers["X-Recon-Token"] == "recon_123"
    assert json.loads(request.content.decode()) == {"cursor": {"last_invoice_id": "inv_123"}}

    assert job.job_id == "job_123"
    assert "scheduled_at" in job.model_dump()


def test_verify_crypto_webhook_signature_success() -> None:
    import hmac
    import hashlib
    import time

    body = {"data": {"invoice_id": "inv_123", "amount": "10.0"}}
    secret = "super-secret"
    timestamp = str(int(time.time()))
    raw_body = json.dumps(body, separators=(",", ":"))
    expected = hmac.new(secret.encode(), f"{timestamp}.{raw_body}".encode(), hashlib.sha256).hexdigest()
    signature = f"t={timestamp},v1={expected}"

    assert verify_crypto_webhook_signature(body=raw_body, signature=signature, secret=secret) is True


def test_verify_crypto_webhook_signature_requires_raw_body() -> None:
    import hmac
    import hashlib
    import time

    body = {"data": {"invoice_id": "inv_123", "amount": "10.0"}}
    secret = "super-secret"
    timestamp = str(int(time.time()))
    raw_body = json.dumps(body, separators=(",", ":"))
    expected = hmac.new(secret.encode(), f"{timestamp}.{raw_body}".encode(), hashlib.sha256).hexdigest()
    signature = f"t={timestamp},v1={expected}"

    with pytest.raises(ValueError) as exc:
        verify_crypto_webhook_signature(body=body, signature=signature, secret=secret)

    assert "raw request body" in str(exc.value).lower()


def test_verify_crypto_webhook_signature_invalid() -> None:
    import time

    body = {"data": {"invoice_id": "inv_123"}}
    secret = "super-secret"
    timestamp = str(int(time.time()))
    signature = f"t={timestamp},v1=deadbeef"

    with pytest.raises(ValueError):
        verify_crypto_webhook_signature(body=body, signature=signature, secret=secret)

@respx.mock
def test_get_wallet_transaction_success(payments_client: payments.PaymentsClient, base_url: str, api_key: str, access_token: str, transaction_status_payload: Dict[str, Any]) -> None:
    route = respx.get(f"{base_url}/api/payments/wallet-transaction/0x123abc").mock(return_value=Response(200, json=transaction_status_payload))

    result = payments_client.get_wallet_transaction(transaction_id="0x123abc")

    assert route.called, "Wallet transaction endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"

    assert result.transaction_id == "0x123abc"
    assert result.status == "confirmed"
    assert result.balance_added == 100.0


@respx.mock
def test_get_wallet_transaction_error(payments_client: payments.PaymentsClient, base_url: str) -> None:
    respx.get(f"{base_url}/api/payments/wallet-transaction/0xmissing").mock(
        return_value=Response(404, json={"success": False, "error": {"code": "TRANSACTION_NOT_FOUND", "message": "Not found"}}),
    )

    with pytest.raises(payments.PaymentsError) as exc:
        payments_client.get_wallet_transaction(transaction_id="0xmissing")

    assert exc.value.status_code == 404
    assert exc.value.error_code == "TRANSACTION_NOT_FOUND"


@respx.mock
def test_get_subscription_success(payments_client: payments.PaymentsClient, base_url: str, api_key: str, access_token: str, subscription_payload: Dict[str, Any]) -> None:
    route = respx.get(f"{base_url}/api/stripe/subscription/sub_1234567890").mock(return_value=Response(200, json=subscription_payload))

    result = payments_client.get_subscription(subscription_id="sub_1234567890")

    assert route.called, "Subscription endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"

    assert result.id == "sub_1234567890"
    assert result.status == "active"
    assert result.items[0].price.recurring.interval == "month"


@respx.mock
def test_get_subscription_error(payments_client: payments.PaymentsClient, base_url: str) -> None:
    respx.get(f"{base_url}/api/stripe/subscription/sub_missing").mock(
        return_value=Response(404, json={"success": False, "error": {"code": "SUBSCRIPTION_NOT_FOUND", "message": "Not found"}}),
    )

    with pytest.raises(payments.PaymentsError) as exc:
        payments_client.get_subscription(subscription_id="sub_missing")

    assert exc.value.status_code == 404
    assert exc.value.error_code == "SUBSCRIPTION_NOT_FOUND"


@respx.mock
def test_cancel_subscription_success(payments_client: payments.PaymentsClient, base_url: str, api_key: str, access_token: str, cancel_subscription_payload: Dict[str, Any]) -> None:
    route = respx.post(f"{base_url}/api/stripe/subscription/sub_1234567890/cancel").mock(return_value=Response(200, json=cancel_subscription_payload))

    result = payments_client.cancel_subscription(
        subscription_id="sub_1234567890",
        immediately=True,
    )

    assert route.called, "Cancel subscription endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    body = json.loads(request.content.decode())
    assert body == {
        "immediately": True,
    }

    assert result.status == "canceled"
    assert result.cancel_at_period_end is True


@respx.mock
def test_cancel_subscription_error(payments_client: payments.PaymentsClient, base_url: str) -> None:
    respx.post(f"{base_url}/api/stripe/subscription/sub_missing/cancel").mock(
        return_value=Response(400, json={"success": False, "error": {"code": "INVALID_SUBSCRIPTION", "message": "Already cancelled"}}),
    )

    with pytest.raises(payments.PaymentsError) as exc:
        payments_client.cancel_subscription(subscription_id="sub_missing")

    assert exc.value.status_code == 400
    assert exc.value.error_code == "INVALID_SUBSCRIPTION"


@respx.mock
def test_list_subscriptions_success(
    payments_client: payments.PaymentsClient,
    base_url: str,
    api_key: str,
    access_token: str,
    subscription_list_payload: Dict[str, Any],
) -> None:
    route = respx.get(f"{base_url}/api/stripe/subscriptions").mock(return_value=Response(200, json=subscription_list_payload))

    result = payments_client.list_subscriptions(status="active", limit=5)

    assert route.called, "List subscriptions endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    params = request.url.params
    assert params["status"] == "active"
    assert params["limit"] == "5"

    assert result.subscriptions[0].id == "sub_1234567890"
    assert result.subscriptions[0].items[0].price.recurring.interval_count == 1
    assert result.has_more is False


@respx.mock
def test_list_subscriptions_error(payments_client: payments.PaymentsClient, base_url: str) -> None:
    respx.get(f"{base_url}/api/stripe/subscriptions").mock(
        return_value=Response(500, json={"success": False, "error": {"code": "SUBSCRIPTION_LIST_ERROR", "message": "Failed to list"}}),
    )

    with pytest.raises(payments.PaymentsError) as exc:
        payments_client.list_subscriptions()

    assert exc.value.status_code == 500
    assert exc.value.error_code == "SUBSCRIPTION_LIST_ERROR"


@respx.mock
def test_update_subscription_success(
    payments_client: payments.PaymentsClient,
    base_url: str,
    api_key: str,
    access_token: str,
    subscription_payload: Dict[str, Any],
) -> None:
    route = respx.post(f"{base_url}/api/stripe/subscription/sub_1234567890/update").mock(return_value=Response(200, json=subscription_payload))

    result = payments_client.update_subscription(subscription_id="sub_1234567890", price_id="price_plus")

    assert route.called, "Update subscription endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    assert json.loads(request.content.decode()) == {"price_id": "price_plus"}

    assert result.id == "sub_1234567890"
    assert result.items[0].price.id == "price_basic"


@respx.mock
def test_update_subscription_error(payments_client: payments.PaymentsClient, base_url: str) -> None:
    respx.post(f"{base_url}/api/stripe/subscription/sub_1234567890/update").mock(
        return_value=Response(400, json={"success": False, "error": {"code": "SUBSCRIPTION_UPDATE_ERROR", "message": "Invalid price"}}),
    )

    with pytest.raises(payments.PaymentsError) as exc:
        payments_client.update_subscription(subscription_id="sub_1234567890", price_id="price_invalid")

    assert exc.value.status_code == 400
    assert exc.value.error_code == "SUBSCRIPTION_UPDATE_ERROR"


@respx.mock
def test_get_checkout_session_success(
    payments_client: payments.PaymentsClient,
    base_url: str,
    api_key: str,
    access_token: str,
    checkout_session_detail_payload: Dict[str, Any],
) -> None:
    route = respx.get(f"{base_url}/api/stripe/checkout-sessions/cs_test_123").mock(return_value=Response(200, json=checkout_session_detail_payload))

    result = payments_client.get_checkout_session(session_id="cs_test_123")

    assert route.called, "Checkout session lookup endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"

    assert result.id == "cs_test_123"
    assert result.payment_status == "paid"
    assert result.client_reference_id == "order_123"


@respx.mock
def test_list_checkout_sessions_success(
    payments_client: payments.PaymentsClient,
    base_url: str,
    api_key: str,
    access_token: str,
    checkout_sessions_list_payload: Dict[str, Any],
) -> None:
    route = respx.get(f"{base_url}/api/stripe/checkout-sessions").mock(return_value=Response(200, json=checkout_sessions_list_payload))

    result = payments_client.list_checkout_sessions(limit=10, starting_after="cs_prev")

    assert route.called, "Checkout sessions list endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    params = request.url.params
    assert params["limit"] == "10"
    assert params["starting_after"] == "cs_prev"

    assert result.sessions[0].id == "cs_test_123"
    assert result.sessions[0].status == "open"
    assert result.has_more is False


@respx.mock
def test_expire_checkout_session_success(
    payments_client: payments.PaymentsClient,
    base_url: str,
    api_key: str,
    access_token: str,
    expire_checkout_session_payload: Dict[str, Any],
) -> None:
    route = respx.post(f"{base_url}/api/stripe/checkout-sessions/cs_test_123/expire").mock(return_value=Response(200, json=expire_checkout_session_payload))

    result = payments_client.expire_checkout_session(session_id="cs_test_123")

    assert route.called, "Checkout session expire endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    assert result.expired is True
    assert result.status == "expired"


@respx.mock
def test_create_guest_checkout_session_success(
    payments_client: payments.PaymentsClient,
    base_url: str,
    api_key: str,
    guest_checkout_create_payload: Dict[str, Any],
) -> None:
    route = respx.post(f"{base_url}/api/stripe/guest-checkout-sessions").mock(return_value=Response(200, json=guest_checkout_create_payload))

    result = payments_client.create_guest_checkout_session(
        customer_email="guest@example.com",
        mode="payment",
        line_items=[{"price_id": "price_basic", "quantity": 1}],
        success_url="https://app.example.com/success",
        cancel_url="https://app.example.com/cancel",
    )

    assert route.called, "Guest checkout creation endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert "Authorization" not in request.headers
    payload = json.loads(request.content.decode())
    assert payload["customer_email"] == "guest@example.com"
    assert payload["mode"] == "payment"

    assert result.id == "cs_test_guest"
    assert result.customer_email == "guest@example.com"
    assert result.client_reference_id == "guest_ref_123"


@respx.mock
def test_get_guest_checkout_session_success(
    payments_client: payments.PaymentsClient,
    base_url: str,
    api_key: str,
    guest_checkout_detail_payload: Dict[str, Any],
) -> None:
    route = respx.get(f"{base_url}/api/stripe/guest-checkout-sessions/cs_test_guest").mock(return_value=Response(200, json=guest_checkout_detail_payload))

    result = payments_client.get_guest_checkout_session(session_id="cs_test_guest")

    assert route.called, "Guest checkout lookup endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert "Authorization" not in request.headers
    assert result.id == "cs_test_guest"
    assert result.payment_status == "paid"
    assert result.metadata["is_guest"] == "true"


@respx.mock
def test_list_guest_checkout_sessions_success(
    payments_client: payments.PaymentsClient,
    base_url: str,
    api_key: str,
    guest_checkout_list_payload: Dict[str, Any],
) -> None:
    route = respx.get(f"{base_url}/api/stripe/guest-checkout-sessions").mock(return_value=Response(200, json=guest_checkout_list_payload))

    result = payments_client.list_guest_checkout_sessions(limit=5, customer_email="guest@example.com")

    assert route.called, "Guest checkout list endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert "Authorization" not in request.headers
    params = request.url.params
    assert params["limit"] == "5"
    assert params["customer_email"] == "guest@example.com"
    assert result.has_more is False
    assert result.sessions[0].session_id == "cs_test_guest"


@respx.mock
def test_convert_guest_checkout_session_success(
    payments_client: payments.PaymentsClient,
    base_url: str,
    api_key: str,
    guest_checkout_convert_payload: Dict[str, Any],
) -> None:
    route = respx.post(f"{base_url}/api/stripe/guest-checkout-sessions/convert").mock(return_value=Response(200, json=guest_checkout_convert_payload))

    result = payments_client.convert_guest_checkout_session(
        session_id="cs_test_guest",
        email="guest@example.com",
        send_magic_link=True,
    )

    assert route.called, "Guest checkout conversion endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert "Authorization" not in request.headers
    assert json.loads(request.content.decode()) == {
        "session_id": "cs_test_guest",
        "email": "guest@example.com",
        "send_magic_link": True,
    }
    assert result.user_id == "user_123"
    assert result.magic_link_sent is True


@respx.mock
def test_list_payment_history_success(
    payments_client: payments.PaymentsClient,
    base_url: str,
    api_key: str,
    access_token: str,
    payment_history_payload: Dict[str, Any],
) -> None:
    route = respx.get(f"{base_url}/api/stripe/history").mock(return_value=Response(200, json=payment_history_payload))

    result = payments_client.list_payment_history(limit=20, status="succeeded")

    assert route.called, "Payment history endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    params = request.url.params
    assert params["limit"] == "20"
    assert params["status"] == "succeeded"
    assert result.payments[0].id == "pi_123"
    assert result.payments[0].invoice_id == "in_123"
    assert result.has_more is False


@respx.mock
def test_list_payment_history_error(payments_client: payments.PaymentsClient, base_url: str) -> None:
    respx.get(f"{base_url}/api/stripe/history").mock(
        return_value=Response(500, json={"success": False, "error": {"code": "PAYMENT_HISTORY_ERROR", "message": "Stripe unavailable"}}),
    )

    with pytest.raises(payments.PaymentsError) as exc:
        payments_client.list_payment_history()

    assert exc.value.status_code == 500
    assert exc.value.error_code == "PAYMENT_HISTORY_ERROR"


@respx.mock
def test_get_payment_detail_success(
    payments_client: payments.PaymentsClient,
    base_url: str,
    api_key: str,
    access_token: str,
    payment_detail_payload: Dict[str, Any],
) -> None:
    route = respx.get(f"{base_url}/api/stripe/payment/pi_123").mock(return_value=Response(200, json=payment_detail_payload))

    result = payments_client.get_payment_detail(payment_id="pi_123")

    assert route.called, "Payment detail endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    assert result.id == "pi_123"
    assert result.amount == 4_200


@respx.mock
def test_get_payment_detail_error(payments_client: payments.PaymentsClient, base_url: str) -> None:
    respx.get(f"{base_url}/api/stripe/payment/pi_missing").mock(
        return_value=Response(404, json={"success": False, "error": {"code": "PAYMENT_NOT_FOUND", "message": "Missing"}}),
    )

    with pytest.raises(payments.PaymentsError) as exc:
        payments_client.get_payment_detail(payment_id="pi_missing")

    assert exc.value.status_code == 404
    assert exc.value.error_code == "PAYMENT_NOT_FOUND"


@respx.mock
def test_list_products_success(
    payments_client: payments.PaymentsClient,
    base_url: str,
    api_key: str,
    access_token: str,
    products_list_payload: Dict[str, Any],
) -> None:
    route = respx.get(f"{base_url}/api/stripe/products").mock(return_value=Response(200, json=products_list_payload))

    result = payments_client.list_products(
        category="billing",
        active=True,
        limit=5,
        starting_after="prod_122",
    )

    assert route.called, "Products endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    params = request.url.params
    assert params["category"] == "billing"
    assert params["active"] == "true"
    assert params["limit"] == "5"
    assert params["starting_after"] == "prod_122"

    assert result.total == 1
    assert result.products[0].name == "Sweet Potato Pro"
    assert result.products[0].prices[0].unit_amount == 2000


@respx.mock
def test_list_products_error(payments_client: payments.PaymentsClient, base_url: str) -> None:
    respx.get(f"{base_url}/api/stripe/products").mock(
        return_value=Response(500, json={"success": False, "error": {"code": "PRODUCT_LIST_ERROR", "message": "Failed"}}),
    )

    with pytest.raises(payments.PaymentsError) as exc:
        payments_client.list_products()

    assert exc.value.status_code == 500
    assert exc.value.error_code == "PRODUCT_LIST_ERROR"


@respx.mock
def test_get_product_success(
    payments_client: payments.PaymentsClient,
    base_url: str,
    api_key: str,
    access_token: str,
    product_detail_payload: Dict[str, Any],
) -> None:
    route = respx.get(f"{base_url}/api/stripe/products/prod_123").mock(return_value=Response(200, json=product_detail_payload))

    product = payments_client.get_product(product_id="prod_123")

    assert route.called, "Product detail endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    assert "include_prices" not in request.url.params

    assert product.id == "prod_123"
    assert product.prices[0].nickname == "Monthly"


@respx.mock
def test_get_product_without_prices(
    payments_client: payments.PaymentsClient,
    base_url: str,
    product_detail_payload: Dict[str, Any],
) -> None:
    route = respx.get(f"{base_url}/api/stripe/products/prod_123").mock(return_value=Response(200, json=product_detail_payload))

    payments_client.get_product(product_id="prod_123", include_prices=False)

    request = route.calls.last.request
    assert request.url.params["include_prices"] == "false"


@respx.mock
def test_get_product_error(payments_client: payments.PaymentsClient, base_url: str) -> None:
    respx.get(f"{base_url}/api/stripe/products/prod_missing").mock(
        return_value=Response(404, json={"success": False, "error": {"code": "NOT_FOUND", "message": "Missing"}}),
    )

    with pytest.raises(payments.PaymentsError) as exc:
        payments_client.get_product(product_id="prod_missing")

    assert exc.value.status_code == 404
    assert exc.value.error_code == "NOT_FOUND"
