import pytest
import pytest_asyncio
import respx
from httpx import Response

from spaps_client import (
    SpapsClient,
    AsyncSpapsClient,
    InMemoryTokenStorage,
)


@pytest.fixture()
def sync_client() -> SpapsClient:
    storage = InMemoryTokenStorage()
    client = SpapsClient(base_url="https://api.sweetpotato.dev", api_key="test_key", token_storage=storage)
    yield client
    client.close()


@pytest_asyncio.fixture()
async def async_client() -> AsyncSpapsClient:
    storage = InMemoryTokenStorage()
    client = AsyncSpapsClient(base_url="https://api.sweetpotato.dev", api_key="test_key", token_storage=storage)
    yield client
    await client.aclose()


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


@respx.mock
def test_sync_smoke_flow(sync_client: SpapsClient, login_payload: dict) -> None:
    base = "https://api.sweetpotato.dev"
    respx.post(f"{base}/api/auth/login").mock(return_value=Response(200, json=login_payload))
    respx.get(f"{base}/api/sessions").mock(return_value=Response(200, json={"data": {"sessions": [], "total": 0}}))
    respx.get(f"{base}/api/metrics/json").mock(return_value=Response(200, json={"uptime_seconds": 10}))

    sync_client.auth.sign_in_with_password(email="user@example.com", password="Secret123!")
    sessions = sync_client.sessions.list_sessions()
    assert sessions.total == 0
    metrics = sync_client.metrics.get_metrics_json()
    assert metrics["uptime_seconds"] == 10


@pytest.mark.asyncio
@respx.mock
async def test_async_smoke_flow(async_client: AsyncSpapsClient, login_payload: dict) -> None:
    base = "https://api.sweetpotato.dev"
    respx.post(f"{base}/api/auth/login").mock(return_value=Response(200, json=login_payload))
    respx.get(f"{base}/api/sessions").mock(return_value=Response(200, json={"data": {"sessions": [], "total": 0}}))
    respx.get(f"{base}/api/metrics/json").mock(return_value=Response(200, json={"uptime_seconds": 20}))

    await async_client.auth.sign_in_with_password(email="user@example.com", password="Secret123!")
    sessions = await async_client.sessions.list_sessions()
    assert sessions.total == 0
    metrics = await async_client.metrics.get_metrics_json()
    assert metrics["uptime_seconds"] == 20
