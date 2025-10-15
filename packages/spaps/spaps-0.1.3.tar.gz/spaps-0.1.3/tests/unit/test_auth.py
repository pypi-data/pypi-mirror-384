import datetime as dt
import json
from typing import Any, Dict

import pytest
import respx
from httpx import Response

from spaps_client import auth
from spaps_client.storage import InMemoryTokenStorage, StoredTokens


@pytest.fixture()
def base_url() -> str:
    return "https://api.sweetpotato.dev"


@pytest.fixture()
def api_key() -> str:
    return "test_key_local_dev_only"


@pytest.fixture()
def token_storage() -> InMemoryTokenStorage:
    return InMemoryTokenStorage()


@pytest.fixture()
def auth_client(base_url: str, api_key: str, token_storage: InMemoryTokenStorage) -> auth.AuthClient:
    return auth.AuthClient(base_url=base_url, api_key=api_key, token_storage=token_storage)


def isoformat(minutes: int) -> str:
    expiry = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=minutes)).replace(microsecond=0)
    return expiry.isoformat().replace("+00:00", "Z")


@pytest.fixture()
def nonce_response_payload() -> Dict[str, Any]:
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
def token_response_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_in": 900,
            "token_type": "Bearer",
            "user": {"id": "user_123", "wallet_address": "0xabc", "chain": "ethereum"},
        },
    }


@pytest.fixture()
def login_response_payload() -> Dict[str, Any]:
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
                "username": "tester",
                "wallets": ["0xabc"],
                "tier": "pro",
            },
        },
    }


@pytest.fixture()
def register_confirmation_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "message": "Registration successful. Please check your email to confirm your account.",
        "data": {
            "user": {
                "id": "user_123",
                "email": "user@example.com",
                "username": "tester",
                "email_confirmed": False,
            }
        },
    }


@pytest.fixture()
def register_autologin_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "message": "Registration and login successful",
        "tokens": {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_in": 900,
        },
        "user": {
            "id": "user_123",
            "email": "user@example.com",
            "username": "tester",
            "phone_number": "123",
            "tier": "basic",
            "wallets": [],
        },
    }


@pytest.fixture()
def magic_link_send_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "message": "Magic link sent successfully. Please check your email.",
        "data": {
            "email": "user@example.com",
            "sent_at": isoformat(0),
        },
    }


@pytest.fixture()
def magic_link_verify_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "message": "Magic link authentication successful",
        "tokens": {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
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
def logout_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "message": "Successfully logged out"
        }
    }


@pytest.fixture()
def password_reset_request_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "message": "If an account with this email exists, a password reset link has been sent.",
        "data": {
            "email": "user@example.com",
            "sent_at": isoformat(0),
        },
    }


@pytest.fixture()
def password_reset_confirm_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "message": "Password reset successfully. You can now log in with your new password.",
    }


@pytest.fixture()
def user_profile_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "user": {
                "id": "user_123",
                "username": "tester",
                "email": "user@example.com",
                "phone_number": "123-456",
                "wallets": [
                    {"wallet_address": "0xabc", "chain_type": "ethereum", "verified": True},
                    {"wallet_address": "Hv3yF8...9kRt4", "chain_type": "solana", "verified": False},
                ],
                "tier": "pro",
                "metadata": {"plan": "pro", "mfa_enabled": True},
            }
        },
    }


@respx.mock
def test_request_nonce_success(auth_client: auth.AuthClient, base_url: str, api_key: str, nonce_response_payload: Dict[str, Any]) -> None:
    route = respx.post(f"{base_url}/api/auth/nonce").mock(
        return_value=Response(200, json=nonce_response_payload),
    )

    result = auth_client.request_nonce(wallet_address="0xabc", chain="ethereum")

    assert route.called, "Nonce endpoint was not called"
    sent_request = route.calls.last.request
    body = json.loads(sent_request.content.decode())
    assert sent_request.headers["X-API-Key"] == api_key
    assert body == {"wallet_address": "0xabc", "chain": "ethereum"}

    assert result.nonce == nonce_response_payload["data"]["nonce"]
    assert result.message == nonce_response_payload["data"]["message"]
    assert result.wallet_address == "0xabc"


@respx.mock
def test_verify_wallet_success(auth_client: auth.AuthClient, base_url: str, api_key: str, token_response_payload: Dict[str, Any]) -> None:
    route = respx.post(f"{base_url}/api/auth/wallet-sign-in").mock(
        return_value=Response(200, json=token_response_payload),
    )

    result = auth_client.verify_wallet(
        wallet_address="0xabc",
        signature="0xsigned",
        message="Sign this message to authenticate with Sweet Potato: abc123",
        chain="ethereum",
    )

    assert route.called, "Wallet sign-in endpoint was not called"
    sent_request = route.calls.last.request
    body = json.loads(sent_request.content.decode())
    assert sent_request.headers["X-API-Key"] == api_key
    assert body == {
        "wallet_address": "0xabc",
        "signature": "0xsigned",
        "message": "Sign this message to authenticate with Sweet Potato: abc123",
        "chain_type": "ethereum",
    }

    assert result.access_token == token_response_payload["data"]["access_token"]
    assert result.refresh_token == token_response_payload["data"]["refresh_token"]
    assert result.user.user_id == "user_123"


@respx.mock
def test_refresh_tokens_raises_on_error(auth_client: auth.AuthClient, base_url: str) -> None:
    respx.post(f"{base_url}/api/auth/refresh").mock(
        return_value=Response(401, json={"success": False, "error": {"code": "INVALID_REFRESH", "message": "Bad token"}}),
    )

    with pytest.raises(auth.AuthError) as exc:
        auth_client.refresh_tokens(refresh_token="bad-refresh")

    assert exc.value.status_code == 401
    assert exc.value.error_code == "INVALID_REFRESH"


@respx.mock
def test_sign_in_with_password_success(auth_client: auth.AuthClient, base_url: str, api_key: str, login_response_payload: Dict[str, Any]) -> None:
    route = respx.post(f"{base_url}/api/auth/login").mock(return_value=Response(200, json=login_response_payload))

    result = auth_client.sign_in_with_password(email="user@example.com", password="Secret123!")

    assert route.called, "Login endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert json.loads(request.content.decode()) == {"email": "user@example.com", "password": "Secret123!"}

    assert result.access_token == "access-token"
    assert result.user.email == "user@example.com"
    assert result.user.tier == "pro"


@respx.mock
def test_sign_in_with_password_stores_tokens(
    auth_client: auth.AuthClient,
    base_url: str,
    login_response_payload: Dict[str, Any],
    token_storage: InMemoryTokenStorage,
) -> None:
    respx.post(f"{base_url}/api/auth/login").mock(return_value=Response(200, json=login_response_payload))

    auth_client.sign_in_with_password(email="user@example.com", password="Secret123!")

    stored = token_storage.load()
    assert stored is not None
    assert stored.access_token == login_response_payload["data"]["access_token"]
    assert stored.refresh_token == login_response_payload["data"]["refresh_token"]


@respx.mock
def test_get_current_user_success(
    auth_client: auth.AuthClient,
    token_storage: InMemoryTokenStorage,
    base_url: str,
    api_key: str,
    user_profile_payload: Dict[str, Any],
) -> None:
    token_storage.save(StoredTokens(access_token="access-token", refresh_token="refresh-token"))
    route = respx.get(f"{base_url}/api/auth/user").mock(return_value=Response(200, json=user_profile_payload))

    profile = auth_client.get_current_user()

    assert profile.id == "user_123"
    assert profile.email == "user@example.com"
    assert len(profile.wallets) == 2
    assert profile.metadata == {"plan": "pro", "mfa_enabled": True}

    assert route.called, "Profile endpoint was not invoked"
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer access-token"
    assert request.headers["X-API-Key"] == api_key


def test_get_current_user_requires_token(auth_client: auth.AuthClient) -> None:
    with pytest.raises(ValueError):
        auth_client.get_current_user()


@respx.mock
def test_request_password_reset_success(
    auth_client: auth.AuthClient,
    base_url: str,
    api_key: str,
    password_reset_request_payload: Dict[str, Any],
) -> None:
    route = respx.post(f"{base_url}/api/auth/password-reset").mock(return_value=Response(200, json=password_reset_request_payload))

    result = auth_client.request_password_reset(email="user@example.com")

    assert route.called, "Password reset endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert json.loads(request.content.decode()) == {"email": "user@example.com"}

    assert result.message.startswith("If an account")
    assert result.email == "user@example.com"
    assert result.sent_at is not None


@respx.mock
def test_request_password_reset_error(auth_client: auth.AuthClient, base_url: str) -> None:
    respx.post(f"{base_url}/api/auth/password-reset").mock(
        return_value=Response(400, json={"success": False, "error": {"code": "INVALID_EMAIL", "message": "Invalid"}}),
    )

    with pytest.raises(auth.AuthError) as exc:
        auth_client.request_password_reset(email="bad-email")

    assert exc.value.status_code == 400
    assert exc.value.error_code == "INVALID_EMAIL"


@respx.mock
def test_confirm_password_reset_success(
    auth_client: auth.AuthClient,
    base_url: str,
    api_key: str,
    password_reset_confirm_payload: Dict[str, Any],
) -> None:
    route = respx.post(f"{base_url}/api/auth/reset-password-confirm").mock(return_value=Response(200, json=password_reset_confirm_payload))

    result = auth_client.confirm_password_reset(token="reset-token", new_password="Sup3rStrong!")

    assert route.called, "Password reset confirm endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert json.loads(request.content.decode()) == {"token": "reset-token", "new_password": "Sup3rStrong!"}
    assert result.message.startswith("Password reset successfully")


@respx.mock
def test_confirm_password_reset_error(auth_client: auth.AuthClient, base_url: str) -> None:
    respx.post(f"{base_url}/api/auth/reset-password-confirm").mock(
        return_value=Response(401, json={"success": False, "error": {"code": "INVALID_TOKEN", "message": "Expired"}}),
    )

    with pytest.raises(auth.AuthError) as exc:
        auth_client.confirm_password_reset(token="bad-token", new_password="Sup3rStrong!")

    assert exc.value.status_code == 401
    assert exc.value.error_code == "INVALID_TOKEN"


@respx.mock
def test_sign_in_with_password_error(auth_client: auth.AuthClient, base_url: str) -> None:
    respx.post(f"{base_url}/api/auth/login").mock(
        return_value=Response(
            401,
            json={"success": False, "error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"}},
            headers={"X-Request-ID": "req_login_error"},
        ),
    )

    with pytest.raises(auth.AuthError) as exc:
        auth_client.sign_in_with_password(email="user@example.com", password="wrong")

    assert exc.value.status_code == 401
    assert exc.value.error_code == "INVALID_CREDENTIALS"
    assert exc.value.request_id == "req_login_error"


@respx.mock
def test_register_requires_confirmation(auth_client: auth.AuthClient, base_url: str, api_key: str, register_confirmation_payload: Dict[str, Any]) -> None:
    route = respx.post(f"{base_url}/api/auth/register").mock(return_value=Response(201, json=register_confirmation_payload))

    result = auth_client.register(email="user@example.com", password="Secret123!", username="tester")

    assert route.called, "Register endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    body = json.loads(request.content.decode())
    assert body == {
        "email": "user@example.com",
        "password": "Secret123!",
        "username": "tester",
    }

    assert result.message.startswith("Registration successful")
    assert result.tokens is None
    assert result.user.email_confirmed is False


@respx.mock
def test_register_auto_login(auth_client: auth.AuthClient, base_url: str, register_autologin_payload: Dict[str, Any]) -> None:
    respx.post(f"{base_url}/api/auth/register").mock(return_value=Response(201, json=register_autologin_payload))

    result = auth_client.register(email="user@example.com", password="Secret123!", username="tester")

    assert result.tokens is not None
    assert result.tokens.access_token == "access-token"
    assert result.user.tier == "basic"


@respx.mock
def test_register_error(auth_client: auth.AuthClient, base_url: str) -> None:
    respx.post(f"{base_url}/api/auth/register").mock(
        return_value=Response(400, json={"success": False, "error": {"code": "EMAIL_ALREADY_EXISTS", "message": "exists"}}),
    )

    with pytest.raises(auth.AuthError) as exc:
        auth_client.register(email="user@example.com", password="Secret123!")

    assert exc.value.status_code == 400
    assert exc.value.error_code == "EMAIL_ALREADY_EXISTS"


@respx.mock
def test_send_magic_link_success(auth_client: auth.AuthClient, base_url: str, api_key: str, magic_link_send_payload: Dict[str, Any]) -> None:
    route = respx.post(f"{base_url}/api/auth/magic-link").mock(return_value=Response(200, json=magic_link_send_payload))

    result = auth_client.send_magic_link(email="user@example.com")

    assert route.called
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert json.loads(request.content.decode()) == {"email": "user@example.com"}

    assert result.message.startswith("Magic link sent")
    assert result.email == "user@example.com"


@respx.mock
def test_send_magic_link_error(auth_client: auth.AuthClient, base_url: str) -> None:
    respx.post(f"{base_url}/api/auth/magic-link").mock(
        return_value=Response(400, json={"success": False, "error": {"code": "MAGIC_LINK_FAILED", "message": "fail"}}),
    )

    with pytest.raises(auth.AuthError) as exc:
        auth_client.send_magic_link(email="user@example.com")

    assert exc.value.status_code == 400
    assert exc.value.error_code == "MAGIC_LINK_FAILED"


@respx.mock
def test_verify_magic_link_success(auth_client: auth.AuthClient, base_url: str, api_key: str, magic_link_verify_payload: Dict[str, Any]) -> None:
    route = respx.post(f"{base_url}/api/auth/verify-magic-link").mock(return_value=Response(200, json=magic_link_verify_payload))

    result = auth_client.verify_magic_link(token="token123", type="magiclink")

    assert route.called
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert json.loads(request.content.decode()) == {"token": "token123", "type": "magiclink"}

    assert result.tokens is not None
    assert result.user.email == "user@example.com"


@respx.mock
def test_verify_magic_link_error(auth_client: auth.AuthClient, base_url: str) -> None:
    respx.post(f"{base_url}/api/auth/verify-magic-link").mock(
        return_value=Response(401, json={"success": False, "error": {"code": "INVALID_TOKEN", "message": "expired"}}),
    )

    with pytest.raises(auth.AuthError) as exc:
        auth_client.verify_magic_link(token="bad", type="magiclink")

    assert exc.value.status_code == 401
    assert exc.value.error_code == "INVALID_TOKEN"


@respx.mock
def test_logout_success(auth_client: auth.AuthClient, base_url: str, api_key: str, logout_payload: Dict[str, Any]) -> None:
    route = respx.post(f"{base_url}/api/auth/logout").mock(return_value=Response(200, json=logout_payload))

    result = auth_client.logout(access_token="access-token")

    assert route.called
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == "Bearer access-token"
    assert result.message == "Successfully logged out"


@respx.mock
def test_logout_uses_stored_token(
    auth_client: auth.AuthClient,
    base_url: str,
    token_storage: InMemoryTokenStorage,
    logout_payload: Dict[str, Any],
) -> None:
    token_storage.save(StoredTokens(access_token="stored-access", refresh_token="stored-refresh"))
    route = respx.post(f"{base_url}/api/auth/logout").mock(return_value=Response(200, json=logout_payload))

    auth_client.logout()

    assert route.called
    sent_request = route.calls.last.request
    assert sent_request.headers["Authorization"] == "Bearer stored-access"
    assert token_storage.load() is None


@respx.mock
def test_logout_error(auth_client: auth.AuthClient, base_url: str) -> None:
    respx.post(f"{base_url}/api/auth/logout").mock(
        return_value=Response(500, json={"success": False, "error": {"code": "SERVER_ERROR", "message": "oops"}}, headers={"X-Request-ID": "req_logout"}),
    )

    with pytest.raises(auth.AuthError) as exc:
        auth_client.logout(access_token="access-token")

    assert exc.value.status_code == 500
    assert exc.value.error_code == "SERVER_ERROR"
    assert exc.value.request_id == "req_logout"
