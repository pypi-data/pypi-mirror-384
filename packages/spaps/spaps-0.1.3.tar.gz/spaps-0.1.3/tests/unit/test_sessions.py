import datetime as dt
import json
from typing import Any, Dict

import pytest
import respx
from httpx import Response

from spaps_client import sessions


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
def sessions_client(base_url: str, api_key: str, access_token: str) -> sessions.SessionsClient:
    return sessions.SessionsClient(base_url=base_url, api_key=api_key, access_token=access_token)


def isoformat(minutes: int) -> str:
    expiry = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=minutes)).replace(microsecond=0)
    return expiry.isoformat().replace("+00:00", "Z")


@pytest.fixture()
def current_session_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "session": {
                "id": "sess_123",
                "user_id": "user_456",
                "application_id": "app_789",
                "tier": "basic",
                "created_at": isoformat(-10),
                "expires_at": isoformat(50),
                "last_activity": isoformat(0),
                "wallets_count": 2,
                "duration_minutes": 600,
                "idle_minutes": 5,
            }
        },
    }


@respx.mock
def test_get_current_session_success(sessions_client: sessions.SessionsClient, base_url: str, api_key: str, access_token: str, current_session_payload: Dict[str, Any]) -> None:
    route = respx.get(f"{base_url}/api/sessions/current").mock(return_value=Response(200, json=current_session_payload))

    result = sessions_client.get_current_session()

    assert route.called, "Current session endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"

    session = result
    assert session.session_id == "sess_123"
    assert session.user_id == "user_456"
    assert session.tier == "basic"


@respx.mock
def test_get_current_session_raises_on_error(sessions_client: sessions.SessionsClient, base_url: str) -> None:
    respx.get(f"{base_url}/api/sessions/current").mock(
        return_value=Response(401, json={"success": False, "error": {"code": "INVALID_SESSION", "message": "Invalid session"}}),
    )

    with pytest.raises(sessions.SessionError) as exc:
        sessions_client.get_current_session()

    assert exc.value.status_code == 401
    assert exc.value.error_code == "INVALID_SESSION"


@pytest.fixture()
def validate_session_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "session": {
                "valid": True,
                "session_id": "sess_123",
                "expires_at": isoformat(50),
                "renewed": False,
            }
        },
    }


@respx.mock
def test_validate_session_success(sessions_client: sessions.SessionsClient, base_url: str, api_key: str, access_token: str, validate_session_payload: Dict[str, Any]) -> None:
    route = respx.post(f"{base_url}/api/sessions/validate").mock(return_value=Response(200, json=validate_session_payload))

    result = sessions_client.validate_session()

    assert route.called, "Validate endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    assert json.loads(request.content.decode()) == {}

    assert result.valid is True
    assert result.session_id == "sess_123"


@respx.mock
def test_validate_session_allows_override_token(base_url: str, api_key: str, access_token: str, validate_session_payload: Dict[str, Any]) -> None:
    override_token = "override-token"
    client = sessions.SessionsClient(base_url=base_url, api_key=api_key, access_token=access_token)
    route = respx.post(f"{base_url}/api/sessions/validate").mock(return_value=Response(200, json=validate_session_payload))

    client.validate_session(access_token_override=override_token)

    request = route.calls.last.request
    assert request.headers["Authorization"] == f"Bearer {override_token}"


@respx.mock
def test_validate_session_raises_on_error(sessions_client: sessions.SessionsClient, base_url: str) -> None:
    respx.post(f"{base_url}/api/sessions/validate").mock(
        return_value=Response(
            403,
            json={"success": False, "error": {"code": "SESSION_REVOKED", "message": "Session revoked"}},
            headers={"X-Request-ID": "req_session_validate"},
        ),
    )

    with pytest.raises(sessions.SessionError) as exc:
        sessions_client.validate_session()

    assert exc.value.status_code == 403
    assert exc.value.error_code == "SESSION_REVOKED"
    assert exc.value.request_id == "req_session_validate"


@pytest.fixture()
def list_sessions_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "sessions": [
                {
                    "id": "sess_123",
                    "user_id": "user_456",
                    "application_id": "app_789",
                    "created_at": isoformat(-120),
                    "last_used": isoformat(-5),
                    "expires_at": isoformat(55),
                    "user_agent": "Mozilla/5.0",
                    "ip_address": "127.0.0.1",
                    "is_current": True,
                },
                {
                    "id": "sess_456",
                    "user_id": "user_456",
                    "application_id": "app_789",
                    "created_at": isoformat(-240),
                    "last_used": isoformat(-30),
                    "expires_at": isoformat(25),
                    "user_agent": "Mozilla/5.0",
                    "ip_address": "192.168.1.10",
                    "is_current": False,
                },
            ],
            "total": 2,
        },
    }


@respx.mock
def test_list_sessions_success(
    sessions_client: sessions.SessionsClient,
    base_url: str,
    api_key: str,
    access_token: str,
    list_sessions_payload: Dict[str, Any],
) -> None:
    route = respx.get(f"{base_url}/api/sessions").mock(return_value=Response(200, json=list_sessions_payload))

    result = sessions_client.list_sessions(limit=25, starting_after="sess_101")

    assert route.called, "List sessions endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    assert request.url.params["limit"] == "25"
    assert request.url.params["starting_after"] == "sess_101"

    assert result.total == 2
    assert len(result.sessions) == 2
    first_session = result.sessions[0]
    assert first_session.session_id == "sess_123"
    assert first_session.is_current is True


@pytest.fixture()
def touch_session_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "message": "Session activity updated",
            "session_id": "sess_123",
            "last_activity": isoformat(0),
        },
    }


@respx.mock
def test_touch_session_success(
    sessions_client: sessions.SessionsClient,
    base_url: str,
    api_key: str,
    access_token: str,
    touch_session_payload: Dict[str, Any],
) -> None:
    route = respx.post(f"{base_url}/api/sessions/touch").mock(return_value=Response(200, json=touch_session_payload))

    result = sessions_client.touch_session()

    assert route.called, "Touch session endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    assert json.loads(request.content.decode()) == {}

    assert result.session_id == "sess_123"
    assert "updated" in result.message


@pytest.fixture()
def revoke_session_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "message": "Session revoked successfully",
            "session_id": "sess_456",
        },
    }


@respx.mock
def test_revoke_session_success(
    sessions_client: sessions.SessionsClient,
    base_url: str,
    api_key: str,
    access_token: str,
    revoke_session_payload: Dict[str, Any],
) -> None:
    route = respx.delete(f"{base_url}/api/sessions/sess_456").mock(return_value=Response(200, json=revoke_session_payload))

    result = sessions_client.revoke_session("sess_456")

    assert route.called, "Revoke session endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"

    assert result.session_id == "sess_456"
    assert "revoked" in result.message


@respx.mock
def test_revoke_session_raises_on_error(sessions_client: sessions.SessionsClient, base_url: str) -> None:
    respx.delete(f"{base_url}/api/sessions/sess_999").mock(
        return_value=Response(404, json={"success": False, "error": {"code": "SESSION_NOT_FOUND", "message": "Session not found"}}),
    )

    with pytest.raises(sessions.SessionError) as exc:
        sessions_client.revoke_session("sess_999")

    assert exc.value.status_code == 404
    assert exc.value.error_code == "SESSION_NOT_FOUND"
