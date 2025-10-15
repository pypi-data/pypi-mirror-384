"""
Shared HTTP utilities for the SPAPS Python client.

Provides retry/backoff helpers and structured logging hooks that wrap httpx.Client.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

import httpx

__all__ = [
    "RetryConfig",
    "LoggingHooks",
    "default_logging_hooks",
    "RetryClient",
]


@dataclass
class RetryConfig:
    """Configuration values controlling retry behaviour."""

    max_attempts: int = 3
    backoff_factor: float = 0.5
    jitter: bool = True
    status_codes: Sequence[int] = (429, 500, 502, 503, 504)
    methods: Sequence[str] = ("GET", "HEAD", "OPTIONS", "DELETE", "PUT")

    def is_retryable(self, request: httpx.Request, response: Optional[httpx.Response]) -> bool:
        if request.method.upper() not in (method.upper() for method in self.methods):
            return False
        if response is None:
            # Retry on transport errors such as timeouts; caller decides per exception.
            return True
        return response.status_code in self.status_codes

    def get_backoff(self, attempt: int) -> float:
        if attempt <= 1:
            delay = 0.0
        else:
            delay = self.backoff_factor * (2 ** (attempt - 2))
        if self.jitter and delay:
            return random.uniform(0, delay)
        return delay


@dataclass
class LoggingHooks:
    """Container for optional logging callbacks."""

    on_request: Optional[Callable[[httpx.Request], None]] = None
    on_response: Optional[Callable[[httpx.Request, httpx.Response, float, int], None]] = None
    on_error: Optional[Callable[[httpx.Request, Exception, int], None]] = None
    on_retry: Optional[Callable[[httpx.Request, int], None]] = None


def default_logging_hooks() -> LoggingHooks:
    """Build logging hooks that emit structured events via the standard logging module."""

    import logging

    logger = logging.getLogger("spaps_client.http")

    def _on_request(request: httpx.Request) -> None:
        logger.debug("HTTP request", extra={"method": request.method, "url": str(request.url)})

    def _on_response(request: httpx.Request, response: httpx.Response, elapsed: float, attempt: int) -> None:
        logger.info(
            "HTTP response",
            extra={
                "method": request.method,
                "url": str(request.url),
                "status": response.status_code,
                "elapsed": elapsed,
                "attempt": attempt,
                "request_id": response.headers.get("x-request-id"),
            },
        )

    def _on_error(request: httpx.Request, exc: Exception, attempt: int) -> None:
        logger.warning(
            "HTTP error",
            extra={"method": request.method, "url": str(request.url), "error": repr(exc), "attempt": attempt},
        )

    def _on_retry(request: httpx.Request, attempt: int) -> None:
        logger.debug("HTTP retry", extra={"method": request.method, "url": str(request.url), "attempt": attempt})

    return LoggingHooks(
        on_request=_on_request,
        on_response=_on_response,
        on_error=_on_error,
        on_retry=_on_retry,
    )


class RetryClient(httpx.Client):
    """
    httpx.Client subclass that adds retry/backoff logic and optional logging hooks.
    """

    def __init__(
        self,
        *,
        retry_config: Optional[RetryConfig] = None,
        logging_hooks: Optional[LoggingHooks] = None,
        **kwargs,
    ) -> None:
        self._retry_config = retry_config
        self._logging_hooks = logging_hooks
        super().__init__(**kwargs)

    def send(self, request: httpx.Request, **kwargs) -> httpx.Response:
        hooks = self._logging_hooks
        if hooks and hooks.on_request:
            hooks.on_request(request)

        original_request = request
        attempt = 1
        retry_conf = self._retry_config
        while True:
            prepared = self._prepare_request(original_request)
            start = time.monotonic()
            try:
                response = super().send(prepared, **kwargs)
            except Exception as exc:  # pragma: no cover - exercised in integration
                if hooks and hooks.on_error:
                    hooks.on_error(original_request, exc, attempt)
                if retry_conf and attempt < retry_conf.max_attempts and retry_conf.is_retryable(original_request, None):
                    self._sleep(retry_conf.get_backoff(attempt + 1))
                    attempt += 1
                    if hooks and hooks.on_retry:
                        hooks.on_retry(original_request, attempt)
                    continue
                raise

            elapsed = time.monotonic() - start
            if hooks and hooks.on_response:
                hooks.on_response(original_request, response, elapsed, attempt)

            if retry_conf and attempt < retry_conf.max_attempts and retry_conf.is_retryable(original_request, response):
                response.close()
                self._sleep(retry_conf.get_backoff(attempt + 1))
                attempt += 1
                if hooks and hooks.on_retry:
                    hooks.on_retry(original_request, attempt)
                continue

            return response

    @staticmethod
    def _sleep(delay: float) -> None:
        if delay > 0:
            time.sleep(delay)

    @staticmethod
    def _prepare_request(request: httpx.Request) -> httpx.Request:
        try:
            content = request.content
        except httpx.RequestNotRead:
            content = request.read()
        headers = list(request.headers.raw)
        return httpx.Request(
            method=request.method,
            url=request.url,
            headers=headers,
            content=content,
            extensions=dict(request.extensions),
        )
