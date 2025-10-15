from typing import Any, Dict

import pytest
import respx
from httpx import Response

from spaps_client.secure_messages import (
    SecureMessagesClient,
    SecureMessagesError,
)


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
def messages_client(base_url: str, api_key: str, access_token: str) -> SecureMessagesClient:
    return SecureMessagesClient(base_url=base_url, api_key=api_key, access_token=access_token)


@pytest.fixture()
def create_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "id": "msg-1d9b80b4",
            "application_id": "app-secure",
            "patient_id": "patient-123",
            "practitioner_id": "practitioner-456",
            "content": "Encrypted payload",
            "metadata": {"urgency": "high"},
            "created_at": "2025-01-15T18:59:00.000Z",
        },
    }


@pytest.fixture()
def list_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "messages": [
                {
                    "id": "msg-1d9b80b4",
                    "application_id": "app-secure",
                    "patient_id": "patient-123",
                    "practitioner_id": "practitioner-456",
                    "content": "Encrypted payload",
                    "metadata": {"urgency": "high"},
                    "created_at": "2025-01-15T18:59:00.000Z",
                }
            ]
        },
    }


@respx.mock
def test_create_secure_message(
    messages_client: SecureMessagesClient,
    base_url: str,
    api_key: str,
    access_token: str,
    create_payload: Dict[str, Any],
) -> None:
    route = respx.post(f"{base_url}/api/secure-messages").mock(return_value=Response(201, json=create_payload))

    message = messages_client.create_message(
        patient_id="patient-123",
        practitioner_id="practitioner-456",
        content="Encrypted payload",
        metadata={"urgency": "high"},
    )

    assert route.called, "Create secure message endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"

    assert message.id == "msg-1d9b80b4"
    assert message.patient_id == "patient-123"
    assert message.metadata == {"urgency": "high"}


@respx.mock
def test_list_secure_messages(
    messages_client: SecureMessagesClient,
    base_url: str,
    api_key: str,
    access_token: str,
    list_payload: Dict[str, Any],
) -> None:
    route = respx.get(f"{base_url}/api/secure-messages").mock(return_value=Response(200, json=list_payload))

    messages = messages_client.list_messages()

    assert route.called, "List secure messages endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"

    assert len(messages) == 1
    assert messages[0].id == "msg-1d9b80b4"


@respx.mock
def test_secure_messages_error(messages_client: SecureMessagesClient, base_url: str) -> None:
    respx.get(f"{base_url}/api/secure-messages").mock(
        return_value=Response(500, json={"success": False, "error": {"code": "SECURE_MESSAGE_LIST_FAILED", "message": "boom"}}),
    )

    with pytest.raises(SecureMessagesError) as exc:
        messages_client.list_messages()

    assert exc.value.status_code == 500
    assert exc.value.error_code == "SECURE_MESSAGE_LIST_FAILED"
