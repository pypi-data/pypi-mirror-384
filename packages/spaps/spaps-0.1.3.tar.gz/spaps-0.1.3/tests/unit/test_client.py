import json

import pytest
import respx
from httpx import Response

from spaps_client.client import SpapsClient
from spaps_client.storage import InMemoryTokenStorage


@pytest.fixture()
def base_url() -> str:
    return "https://api.sweetpotato.dev"


@pytest.fixture()
def api_key() -> str:
    return "test_key_local_dev_only"


@pytest.fixture()
def storage() -> InMemoryTokenStorage:
    return InMemoryTokenStorage()


@pytest.fixture()
def client(base_url: str, api_key: str, storage: InMemoryTokenStorage) -> SpapsClient:
    sdk = SpapsClient(base_url=base_url, api_key=api_key, token_storage=storage)
    yield sdk
    sdk.close()


@pytest.fixture()
def login_payload() -> dict:
    return {
        "success": True,
        "data": {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_in": 900,
            "token_type": "Bearer",
            "user": {
                "id": "user_123",
                "email": "user@example.com",
                "tier": "pro",
            },
        },
    }


@pytest.fixture()
def list_sessions_payload() -> dict:
    return {
        "success": True,
        "data": {
            "sessions": [
                {
                    "id": "sess_123",
                    "user_id": "user_123",
                    "application_id": "app_123",
                    "created_at": "2025-01-01T00:00:00Z",
                    "expires_at": "2025-01-02T00:00:00Z",
                    "last_used": "2025-01-01T10:00:00Z",
                    "is_current": True,
                }
            ],
            "total": 1,
        },
    }


@respx.mock
def test_builder_persists_tokens(
    client: SpapsClient,
    base_url: str,
    api_key: str,
    login_payload: dict,
    storage: InMemoryTokenStorage,
) -> None:
    respx.post(f"{base_url}/api/auth/login").mock(return_value=Response(200, json=login_payload))

    tokens = client.auth.sign_in_with_password(email="user@example.com", password="Secret123!")

    stored = storage.load()
    assert stored is not None
    assert stored.access_token == "access-token"
    assert tokens.access_token == "access-token"

    sessions_route = respx.get(f"{base_url}/api/sessions").mock(
        return_value=Response(200, json={"data": {"sessions": [], "total": 0}})
    )

    client.sessions.list_sessions()
    request = sessions_route.calls.last.request
    assert request.headers["Authorization"] == "Bearer access-token"
    assert request.headers["X-API-Key"] == api_key


@respx.mock
def test_set_tokens_exposes_payments_client(
    client: SpapsClient,
    base_url: str,
    api_key: str,
) -> None:
    client.set_tokens(access_token="stored-access")

    payload = {
        "success": True,
        "data": {
            "session_id": "cs_test",
            "checkout_url": "https://checkout.stripe.com/pay/cs_test",
        },
    }
    route = respx.post(f"{base_url}/api/payments/create-checkout-session").mock(
        return_value=Response(200, json=payload)
    )

    client.payments.create_checkout_session(
        price_id="price_123",
        mode="subscription",
        success_url="https://example.com/success",
        cancel_url="https://example.com/cancel",
    )

    sent = json.loads(route.calls.last.request.content.decode())
    assert sent["price_id"] == "price_123"
    assert route.calls.last.request.headers["Authorization"] == "Bearer stored-access"
