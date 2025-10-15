import json
from typing import Any, Dict

import pytest
import respx
from httpx import Response

from spaps_client.usage import (
    UsageClient,
    UsageError,
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
def usage_client(base_url: str, api_key: str, access_token: str) -> UsageClient:
    return UsageClient(base_url=base_url, api_key=api_key, access_token=access_token)


@pytest.fixture()
def features_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "user_id": "user_123",
            "tier": "premium",
            "period": {
                "start": "2025-01-01T00:00:00Z",
                "end": "2025-01-31T23:59:59Z",
            },
            "features": [
                {
                    "name": "api_calls",
                    "description": "Total API calls",
                    "used": 8500,
                    "limit": 10000,
                    "percentage": 85,
                    "reset_at": "2025-02-01T00:00:00Z",
                }
            ],
            "overage": {
                "allowed": True,
                "charges": [],
            },
        },
    }


@pytest.fixture()
def record_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "record_id": "usage_abc123",
            "feature": "api_calls",
            "quantity": 5,
            "recorded_at": "2025-01-09T10:30:00Z",
            "current_usage": {
                "used": 8510,
                "limit": 10000,
                "remaining": 1490,
            },
            "warning": None,
        },
    }


@pytest.fixture()
def history_payload() -> Dict[str, Any]:
    return {
        "success": True,
        "data": {
            "period": "daily",
            "start_date": "2025-01-01",
            "end_date": "2025-01-03",
            "history": [
                {
                    "date": "2025-01-01",
                    "features": {
                        "api_calls": 320,
                        "wallet_verifications": 12,
                    },
                    "total_cost": 0,
                }
            ],
            "summary": {
                "total_api_calls": 8501,
                "total_wallet_verifications": 150,
                "total_cost": 0,
            },
        },
    }


@respx.mock
def test_get_usage_features_success(
    usage_client: UsageClient,
    base_url: str,
    api_key: str,
    access_token: str,
    features_payload: Dict[str, Any],
) -> None:
    route = respx.get(f"{base_url}/api/usage/features").mock(return_value=Response(200, json=features_payload))

    result = usage_client.get_features()

    assert route.called, "Usage features endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"

    assert result.user_id == "user_123"
    assert result.features[0].name == "api_calls"
    assert result.features[0].used == 8500


@respx.mock
def test_get_usage_features_error(usage_client: UsageClient, base_url: str) -> None:
    respx.get(f"{base_url}/api/usage/features").mock(
        return_value=Response(503, json={"success": False, "error": {"code": "USAGE_SERVICE_UNAVAILABLE", "message": "Down for maintenance"}}),
    )

    with pytest.raises(UsageError) as exc:
        usage_client.get_features()

    assert exc.value.status_code == 503
    assert exc.value.error_code == "USAGE_SERVICE_UNAVAILABLE"


@respx.mock
def test_record_usage_success(
    usage_client: UsageClient,
    base_url: str,
    api_key: str,
    access_token: str,
    record_payload: Dict[str, Any],
) -> None:
    route = respx.post(f"{base_url}/api/usage/record").mock(return_value=Response(200, json=record_payload))

    result = usage_client.record_usage(
        feature="api_calls",
        quantity=5,
        metadata={"endpoint": "/api/auth/verify-wallet"},
        timestamp="2025-01-09T10:30:00Z",
        idempotency_key="req_123456",
    )

    assert route.called, "Record usage endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    assert request.headers["X-Idempotency-Key"] == "req_123456"
    body = json.loads(request.content.decode())
    assert body["feature"] == "api_calls"
    assert body["quantity"] == 5
    assert body["metadata"] == {"endpoint": "/api/auth/verify-wallet"}
    assert body["timestamp"] == "2025-01-09T10:30:00Z"

    assert result.feature == "api_calls"
    assert result.current_usage.used == 8510


@respx.mock
def test_get_usage_history_success(
    usage_client: UsageClient,
    base_url: str,
    api_key: str,
    access_token: str,
    history_payload: Dict[str, Any],
) -> None:
    route = respx.get(f"{base_url}/api/usage/history").mock(return_value=Response(200, json=history_payload))

    result = usage_client.get_history(
        period="daily",
        start_date="2025-01-01",
        end_date="2025-01-03",
        feature="api_calls",
    )

    assert route.called, "Usage history endpoint not called"
    request = route.calls.last.request
    assert request.headers["X-API-Key"] == api_key
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    assert request.url.params["period"] == "daily"
    assert request.url.params["start_date"] == "2025-01-01"
    assert request.url.params["end_date"] == "2025-01-03"
    assert request.url.params["feature"] == "api_calls"

    assert result.period == "daily"
    assert result.history[0].date == "2025-01-01"
    assert result.history[0].features["api_calls"] == 320
