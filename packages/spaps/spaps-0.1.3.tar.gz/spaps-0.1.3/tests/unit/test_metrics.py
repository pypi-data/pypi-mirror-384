from typing import Any, Dict

import pytest
import respx
from httpx import Response

from spaps_client.metrics import MetricsClient


@pytest.fixture()
def base_url() -> str:
    return "https://api.sweetpotato.dev"


@pytest.fixture()
def metrics_client(base_url: str) -> MetricsClient:
    return MetricsClient(base_url=base_url)


@pytest.fixture()
def metrics_payload() -> Dict[str, Any]:
    return {
        "timestamp": "2025-01-09T10:30:00Z",
        "uptime_seconds": 864000,
        "system": {"memory": {"rss_mb": 93.6}},
    }


@respx.mock
def test_get_prometheus_metrics(metrics_client: MetricsClient, base_url: str) -> None:
    payload = "# HELP http_requests_total Total HTTP requests received\nhttp_requests_total 123"
    route = respx.get(f"{base_url}/api/metrics").mock(return_value=Response(200, text=payload))

    text = metrics_client.get_prometheus_metrics()

    assert route.called, "Prometheus metrics endpoint not called"
    request = route.calls.last.request
    assert request.headers["Accept"] == "text/plain"
    assert "http_requests_total" in text


@respx.mock
def test_get_metrics_json(metrics_client: MetricsClient, base_url: str, metrics_payload: Dict[str, Any]) -> None:
    route = respx.get(f"{base_url}/api/metrics/json").mock(return_value=Response(200, json=metrics_payload))

    data = metrics_client.get_metrics_json()

    assert route.called, "JSON metrics endpoint not called"
    request = route.calls.last.request
    assert request.headers["Accept"] == "application/json"
    assert data["uptime_seconds"] == 864000


@respx.mock
def test_health_check(metrics_client: MetricsClient, base_url: str) -> None:
    route = respx.get(f"{base_url}/health").mock(return_value=Response(200, json={"status": "healthy"}))

    payload = metrics_client.health()

    assert route.called, "Health endpoint not called"
    assert payload["status"] == "healthy"


@respx.mock
def test_readiness_check(metrics_client: MetricsClient, base_url: str) -> None:
    route = respx.get(f"{base_url}/health/ready").mock(return_value=Response(200, json={"ready": True}))

    payload = metrics_client.readiness()

    assert route.called, "Readiness endpoint not called"
    assert payload["ready"] is True
