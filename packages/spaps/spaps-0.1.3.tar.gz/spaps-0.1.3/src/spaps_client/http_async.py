"""
Async HTTP utilities mirroring the synchronous retry client.
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional

import httpx

from .http import LoggingHooks, RetryConfig

__all__ = ["RetryAsyncClient"]


class RetryAsyncClient(httpx.AsyncClient):
    """Async client that applies retry/backoff behaviour with optional logging hooks."""

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

    async def send(self, request: httpx.Request, **kwargs) -> httpx.Response:
        hooks = self._logging_hooks
        if hooks and hooks.on_request:
            hooks.on_request(request)

        original_request = request
        attempt = 1
        retry_conf = self._retry_config
        while True:
            prepared = await self._prepare_request(original_request)
            start = time.monotonic()
            try:
                response = await super().send(prepared, **kwargs)
            except Exception as exc:
                if hooks and hooks.on_error:
                    hooks.on_error(original_request, exc, attempt)
                if retry_conf and attempt < retry_conf.max_attempts and retry_conf.is_retryable(original_request, None):
                    await self._sleep(retry_conf.get_backoff(attempt + 1))
                    attempt += 1
                    if hooks and hooks.on_retry:
                        hooks.on_retry(original_request, attempt)
                    continue
                raise

            elapsed = time.monotonic() - start
            if hooks and hooks.on_response:
                hooks.on_response(original_request, response, elapsed, attempt)

            if retry_conf and attempt < retry_conf.max_attempts and retry_conf.is_retryable(original_request, response):
                await response.aclose()
                await self._sleep(retry_conf.get_backoff(attempt + 1))
                attempt += 1
                if hooks and hooks.on_retry:
                    hooks.on_retry(original_request, attempt)
                continue

            return response

    @staticmethod
    async def _sleep(delay: float) -> None:
        if delay > 0:
            await asyncio.sleep(delay)

    async def _prepare_request(self, request: httpx.Request) -> httpx.Request:
        try:
            content = request.content
        except httpx.RequestNotRead:
            content = await request.aread()
        headers = list(request.headers.raw)
        return httpx.Request(
            method=request.method,
            url=request.url,
            headers=headers,
            content=content,
            extensions=dict(request.extensions),
        )
