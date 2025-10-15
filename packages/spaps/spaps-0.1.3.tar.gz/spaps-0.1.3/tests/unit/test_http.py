from typing import List, Tuple

import httpx
import pytest
import respx
from httpx import Response

from spaps_client.http import LoggingHooks, RetryClient, RetryConfig


@respx.mock
def test_retry_client_retries_on_500() -> None:
    base_url = "https://api.sweetpotato.dev"
    route = respx.get(f"{base_url}/ping").mock(
        side_effect=[
            Response(500, json={"error": "fail"}),
            Response(200, json={"ok": True}),
        ]
    )

    client = RetryClient(base_url=base_url, retry_config=RetryConfig(max_attempts=3, backoff_factor=0.0))
    response = client.get("/ping")
    client.close()

    assert route.call_count == 2
    assert response.status_code == 200
    assert response.json()["ok"] is True


@respx.mock
def test_logging_hooks_capture_events(monkeypatch: pytest.MonkeyPatch) -> None:
    base_url = "https://api.sweetpotato.dev"
    respx.get(f"{base_url}/ping").mock(return_value=Response(200, json={"ok": True}))

    events: List[Tuple[str, int]] = []

    hooks = LoggingHooks(
        on_request=lambda request: events.append(("request", 0)),
        on_response=lambda request, response, elapsed, attempt: events.append(("response", attempt)),
        on_error=lambda request, exc, attempt: events.append(("error", attempt)),
        on_retry=lambda request, attempt: events.append(("retry", attempt)),
    )

    client = RetryClient(base_url=base_url, logging_hooks=hooks)
    client.get("/ping")
    client.close()

    assert ("request", 0) in events
    assert ("response", 1) in events


@respx.mock
def test_retry_respects_max_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    base_url = "https://api.sweetpotato.dev"
    route = respx.get(f"{base_url}/ping").mock(return_value=Response(503, json={"error": "busy"}))

    attempts: List[int] = []

    def on_retry(request, attempt: int) -> None:
        attempts.append(attempt)

    hooks = LoggingHooks(on_retry=on_retry)
    client = RetryClient(base_url=base_url, retry_config=RetryConfig(max_attempts=2, backoff_factor=0.0), logging_hooks=hooks)

    response = client.get("/ping")
    client.close()

    assert response.status_code == 503
    assert attempts == [2]
    assert route.call_count == 2


class _SingleUseStream(httpx.SyncByteStream):
    """Byte stream helper that raises if iterated more than once."""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self.iterations = 0

    def __iter__(self):  # type: ignore[override]
        if self.iterations:
            raise AssertionError("stream was iterated multiple times")
        self.iterations += 1
        yield self._payload

    def close(self) -> None:  # pragma: no cover - no close behaviour required
        return None


@respx.mock
def test_retry_client_handles_streaming_request_bodies() -> None:
    base_url = "https://api.sweetpotato.dev"
    route = respx.post(f"{base_url}/stream").mock(
        side_effect=[
            Response(503, json={"error": "temporary"}),
            Response(200, json={"ok": True}),
        ]
    )

    client = RetryClient(
        base_url=base_url,
        retry_config=RetryConfig(max_attempts=2, backoff_factor=0.0, methods=("POST",)),
    )

    payload = b"chunk"
    stream = _SingleUseStream(payload)

    response = client.post("/stream", content=stream)
    client.close()

    assert response.status_code == 200
    assert route.call_count == 2

    observed_bodies = [call.request.content for call in route.calls]
    assert observed_bodies == [payload, payload]
    assert stream.iterations == 1
