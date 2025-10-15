import json

import pytest
import respx
from httpx import Response

from spaps_client import whitelist


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
def whitelist_client(base_url: str, api_key: str, access_token: str) -> whitelist.WhitelistClient:
    return whitelist.WhitelistClient(base_url=base_url, api_key=api_key, access_token=access_token)


@respx.mock
def test_check_whitelist_entry(whitelist_client: whitelist.WhitelistClient, base_url: str, api_key: str) -> None:
    payload = {
        "success": True,
        "message": "Magic",
        "data": {
            "entry": {
                "email": "user@example.com",
                "application_id": "app_123",
                "tier": "premium",
                "bypass_payment": True,
            },
            "message": "Email user@example.com is whitelisted with tier: premium",
        },
    }
    route = respx.get(f"{base_url}/api/v1/whitelist/check").mock(return_value=Response(200, json=payload))

    result = whitelist_client.check(email="user@example.com")

    assert route.called
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.url.params["email"] == "user@example.com"

    assert result.entry is not None
    assert result.entry.tier == "premium"


@respx.mock
def test_check_whitelist_not_found(whitelist_client: whitelist.WhitelistClient, base_url: str) -> None:
    payload = {
        "success": True,
        "message": "Magic",
        "data": {
            "message": "Email user@example.com is not whitelisted"
        },
    }
    respx.get(f"{base_url}/api/v1/whitelist/check").mock(return_value=Response(200, json=payload))

    result = whitelist_client.check(email="user@example.com")
    assert result.entry is None
    assert "not whitelisted" in result.message


@respx.mock
def test_add_whitelist_entry(whitelist_client: whitelist.WhitelistClient, base_url: str, api_key: str, access_token: str) -> None:
    payload = {
        "success": True,
        "data": {
            "entry": {
                "email": "user@example.com",
                "application_id": "app_123",
                "tier": "premium",
                "bypass_payment": True,
            }
        }
    }
    route = respx.post(f"{base_url}/api/v1/whitelist").mock(return_value=Response(201, json=payload))

    entry = whitelist_client.add(email="user@example.com", tier="premium", bypass_payment=True)

    assert route.called
    request = route.calls.last.request
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    assert request.headers["X-API-Key"] == api_key
    assert json.loads(request.content.decode())["email"] == "user@example.com"
    assert entry.email == "user@example.com"


@respx.mock
def test_add_whitelist_requires_token(base_url: str, api_key: str) -> None:
    client = whitelist.WhitelistClient(base_url=base_url, api_key=api_key)

    with pytest.raises(ValueError):
        client.add(email="user@example.com")


@respx.mock
def test_list_whitelist_entries(whitelist_client: whitelist.WhitelistClient, base_url: str) -> None:
    payload = {
        "success": True,
        "data": {
            "entries": [
                {"email": "a@example.com", "application_id": "app", "tier": "basic"},
                {"email": "b@example.com", "application_id": "app", "tier": "premium"},
            ],
            "total": 2,
        },
    }
    route = respx.get(f"{base_url}/api/v1/whitelist").mock(return_value=Response(200, json=payload))

    result = whitelist_client.list(limit=2, offset=0)

    assert route.called
    request = route.calls.last.request
    assert request.url.params["limit"] == "2"
    assert result.total == 2
    assert len(result.entries) == 2


@respx.mock
def test_update_whitelist_entry(whitelist_client: whitelist.WhitelistClient, base_url: str) -> None:
    payload = {
        "success": True,
        "data": {
            "entry": {
                "email": "user@example.com",
                "application_id": "app_123",
                "tier": "enterprise",
                "bypass_payment": False,
            }
        }
    }
    route = respx.put(f"{base_url}/api/v1/whitelist/user@example.com").mock(return_value=Response(200, json=payload))

    entry = whitelist_client.update(email="user@example.com", tier="enterprise", bypass_payment=False)

    assert route.called
    request = route.calls.last.request
    assert json.loads(request.content.decode())["tier"] == "enterprise"
    assert entry.tier == "enterprise"


@respx.mock
def test_remove_whitelist_entry(whitelist_client: whitelist.WhitelistClient, base_url: str) -> None:
    payload = {
        "success": True,
        "data": {"message": "Email user@example.com removed from whitelist"}
    }
    route = respx.delete(f"{base_url}/api/v1/whitelist/user@example.com").mock(return_value=Response(200, json=payload))

    message = whitelist_client.remove(email="user@example.com")

    assert route.called
    assert "removed" in message.message


@respx.mock
def test_whitelist_error(whitelist_client: whitelist.WhitelistClient, base_url: str) -> None:
    respx.post(f"{base_url}/api/v1/whitelist").mock(return_value=Response(500, json={"error": {"code": "INTERNAL_ERROR", "message": "boom"}}))

    with pytest.raises(whitelist.WhitelistError) as exc:
        whitelist_client.add(email="user@example.com", tier="basic", bypass_payment=False)

    assert exc.value.status_code == 500
    assert exc.value.error_code == "INTERNAL_ERROR"
