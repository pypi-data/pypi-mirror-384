import json
import datetime as dt

import pytest
import pytest_asyncio
import respx
from httpx import Response

from spaps_client import AsyncSpapsClient, InMemoryTokenStorage


@pytest_asyncio.fixture()
async def async_client() -> AsyncSpapsClient:
    storage = InMemoryTokenStorage()
    client = AsyncSpapsClient(
        base_url="https://api.sweetpotato.dev",
        api_key="test_key_local_dev_only",
        token_storage=storage,
    )
    yield client
    await client.aclose()


"""Return token storage for tests."""

@pytest.fixture()
def storage(async_client: AsyncSpapsClient) -> InMemoryTokenStorage:
    return async_client.token_storage  # type: ignore[return-value]


@pytest.fixture()
def login_payload() -> dict:
    return {
        "success": True,
        "data": {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_in": 900,
            "token_type": "Bearer",
            "user": {"id": "user_123", "email": "user@example.com"},
        },
    }


def isoformat(minutes: int) -> str:
    expiry = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=minutes)).replace(microsecond=0)
    return expiry.isoformat().replace("+00:00", "Z")


@pytest.fixture()
def nonce_payload() -> dict:
    return {
        "success": True,
        "data": {
            "nonce": "Sign this message to authenticate with Sweet Potato: abc123",
            "message": "Sign this message to authenticate with Sweet Potato: abc123",
            "wallet_address": "0xabc",
            "expires_at": isoformat(5),
        },
    }


@pytest.fixture()
def wallet_login_payload() -> dict:
    return {
        "success": True,
        "data": {
            "access_token": "wallet-access",
            "refresh_token": "wallet-refresh",
            "expires_in": 900,
            "token_type": "Bearer",
            "user": {"id": "user_123", "wallet_address": "0xabc", "chain": "ethereum"},
        },
    }


@pytest.fixture()
def magic_link_send_payload() -> dict:
    return {
        "success": True,
        "message": "Magic link sent successfully. Please check your email.",
        "data": {
            "email": "user@example.com",
            "sent_at": isoformat(0),
        },
    }


@pytest.fixture()
def magic_link_verify_payload() -> dict:
    return {
        "success": True,
        "message": "Magic link authentication successful",
        "tokens": {
            "access_token": "magic-access",
            "refresh_token": "magic-refresh",
            "expires_in": 900,
        },
        "user": {
            "id": "user_123",
            "email": "user@example.com",
            "username": "tester",
            "tier": "basic",
            "wallets": [],
        },
    }


@pytest.fixture()
def password_reset_request_payload() -> dict:
    return {
        "success": True,
        "message": "If an account with this email exists, a password reset link has been sent.",
        "data": {
            "email": "user@example.com",
            "sent_at": isoformat(0),
        },
    }


@pytest.fixture()
def password_reset_confirm_payload() -> dict:
    return {
        "success": True,
        "message": "Password reset successfully. You can now log in with your new password.",
    }


@pytest.mark.asyncio
@respx.mock
async def test_async_sign_in_persists_tokens(async_client: AsyncSpapsClient, storage: InMemoryTokenStorage, login_payload: dict) -> None:
    base_url = "https://api.sweetpotato.dev"
    respx.post(f"{base_url}/api/auth/login").mock(return_value=Response(200, json=login_payload))
    respx.get(f"{base_url}/api/sessions").mock(return_value=Response(200, json={"data": {"sessions": [], "total": 0}}))

    tokens = await async_client.auth.sign_in_with_password(email="user@example.com", password="Secret123!")
    assert tokens.access_token == "access-token"
    stored = storage.load()
    assert stored is not None
    assert stored.access_token == "access-token"

    await async_client.sessions.list_sessions()


@pytest.mark.asyncio
@respx.mock
async def test_async_request_password_reset(
    async_client: AsyncSpapsClient,
    password_reset_request_payload: dict,
) -> None:
    base_url = "https://api.sweetpotato.dev"
    route = respx.post(f"{base_url}/api/auth/password-reset").mock(return_value=Response(200, json=password_reset_request_payload))

    result = await async_client.auth.request_password_reset(email="user@example.com")

    assert route.called, "Password reset endpoint not called"
    request = route.calls.last.request
    assert json.loads(request.content.decode()) == {"email": "user@example.com"}
    assert result.email == "user@example.com"


@pytest.mark.asyncio
@respx.mock
async def test_async_confirm_password_reset(
    async_client: AsyncSpapsClient,
    password_reset_confirm_payload: dict,
) -> None:
    base_url = "https://api.sweetpotato.dev"
    route = respx.post(f"{base_url}/api/auth/reset-password-confirm").mock(return_value=Response(200, json=password_reset_confirm_payload))

    result = await async_client.auth.confirm_password_reset(token="reset-token", new_password="Sup3rStrong!")

    assert route.called, "Password reset confirm endpoint not called"
    request = route.calls.last.request
    assert json.loads(request.content.decode()) == {"token": "reset-token", "new_password": "Sup3rStrong!"}
    assert result.message.startswith("Password reset successfully")


@pytest.mark.asyncio
@respx.mock
async def test_async_payments_uses_stored_token(async_client: AsyncSpapsClient) -> None:
    base_url = "https://api.sweetpotato.dev"
    async_client.set_tokens(access_token="stored-access")

    payload = {
        "success": True,
        "data": {
            "session_id": "cs_test",
            "checkout_url": "https://checkout.stripe.com/pay/cs_test",
        },
    }
    route = respx.post(f"{base_url}/api/payments/create-checkout-session").mock(return_value=Response(200, json=payload))

    await async_client.payments.create_checkout_session(
        price_id="price_123",
        mode="subscription",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
    )

    sent_request = route.calls.last.request
    assert json.loads(sent_request.content.decode())["price_id"] == "price_123"
    assert sent_request.headers["Authorization"] == "Bearer stored-access"


@pytest.mark.asyncio
@respx.mock
async def test_async_payments_crypto(async_client: AsyncSpapsClient) -> None:
    base_url = "https://api.sweetpotato.dev"
    async_client.set_tokens(access_token="stored-access")

    payload = {
        "success": True,
        "data": {
            "invoice": {
                "id": "inv_123",
                "asset": "USDC",
                "network": "base",
                "amount": "10",
                "status": "pending",
            }
        },
    }
    route = respx.post(f"{base_url}/api/payments/crypto/invoices").mock(return_value=Response(200, json=payload))

    invoice = await async_client.payments.crypto.create_invoice(asset="USDC", network="base", amount="10")
    assert invoice.invoice_id == "inv_123"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_async_request_nonce(async_client: AsyncSpapsClient, nonce_payload: dict) -> None:
    base_url = "https://api.sweetpotato.dev"
    route = respx.post(f"{base_url}/api/auth/nonce").mock(return_value=Response(200, json=nonce_payload))

    result = await async_client.auth.request_nonce(wallet_address="0xabc", chain="ethereum")

    assert route.called
    sent_request = route.calls.last.request
    body = json.loads(sent_request.content.decode())
    assert body == {"wallet_address": "0xabc", "chain": "ethereum"}
    assert result.wallet_address == "0xabc"
    assert result.nonce == nonce_payload["data"]["nonce"]


@pytest.mark.asyncio
@respx.mock
async def test_async_verify_wallet_stores_tokens(
    async_client: AsyncSpapsClient,
    storage: InMemoryTokenStorage,
    wallet_login_payload: dict,
) -> None:
    base_url = "https://api.sweetpotato.dev"
    route = respx.post(f"{base_url}/api/auth/wallet-sign-in").mock(return_value=Response(200, json=wallet_login_payload))

    tokens = await async_client.auth.verify_wallet(
        wallet_address="0xabc",
        signature="0xsigned",
        message="Sign this message to authenticate with Sweet Potato: abc123",
        chain="ethereum",
    )

    assert route.called
    sent_request = route.calls.last.request
    body = json.loads(sent_request.content.decode())
    assert body == {
        "wallet_address": "0xabc",
        "signature": "0xsigned",
        "message": "Sign this message to authenticate with Sweet Potato: abc123",
        "chain_type": "ethereum",
    }

    stored = storage.load()
    assert stored is not None
    assert stored.access_token == wallet_login_payload["data"]["access_token"]
    assert tokens.access_token == wallet_login_payload["data"]["access_token"]


@pytest.mark.asyncio
@respx.mock
async def test_async_send_magic_link(async_client: AsyncSpapsClient, magic_link_send_payload: dict) -> None:
    base_url = "https://api.sweetpotato.dev"
    route = respx.post(f"{base_url}/api/auth/magic-link").mock(return_value=Response(200, json=magic_link_send_payload))

    result = await async_client.auth.send_magic_link(email="user@example.com")

    assert route.called
    request = route.calls.last.request
    assert json.loads(request.content.decode()) == {"email": "user@example.com"}
    assert result.message == "Magic link sent successfully. Please check your email."
    assert result.email == "user@example.com"


@pytest.mark.asyncio
@respx.mock
async def test_async_verify_magic_link_stores_tokens(
    async_client: AsyncSpapsClient,
    storage: InMemoryTokenStorage,
    magic_link_verify_payload: dict,
) -> None:
    base_url = "https://api.sweetpotato.dev"
    respx.post(f"{base_url}/api/auth/verify-magic-link").mock(return_value=Response(200, json=magic_link_verify_payload))

    result = await async_client.auth.verify_magic_link(token="token123", type="magiclink")

    stored = storage.load()
    assert stored is not None
    assert stored.access_token == "magic-access"
    assert result.user.email == "user@example.com"


@pytest.mark.asyncio
@respx.mock
async def test_async_metrics(async_client: AsyncSpapsClient) -> None:
    base_url = "https://api.sweetpotato.dev"
    respx.get(f"{base_url}/health").mock(return_value=Response(200, json={"status": "ok"}))
    payload = await async_client.metrics.health()
    assert payload["status"] == "ok"
