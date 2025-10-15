"""
Configuration utilities for the SPAPS Python client.

Provides environment-driven defaults and helpers for constructing shared HTTP
client instances with consistent timeouts.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import httpx

from .http import LoggingHooks, RetryClient, RetryConfig

__all__ = ["Settings", "create_http_client"]

DEFAULT_BASE_URL = "http://localhost:3300"
DEFAULT_API_KEY = "test_key_local_dev_only"
DEFAULT_TIMEOUT = 10.0


@dataclass
class Settings:
    """
    Container for configuring API access.

    Fields default to environment variables, falling back to sensible local
    development defaults when unspecified.
    """

    base_url: str = DEFAULT_BASE_URL
    api_key: str = DEFAULT_API_KEY
    request_timeout: float = DEFAULT_TIMEOUT

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        request_timeout: Optional[float] = None,
    ) -> None:
        env_base = os.getenv("SPAPS_API_URL")
        env_key = os.getenv("SPAPS_API_KEY")
        self.base_url = base_url if base_url is not None else (env_base or DEFAULT_BASE_URL)
        self.api_key = api_key if api_key is not None else (env_key or DEFAULT_API_KEY)
        if request_timeout is not None:
            self.request_timeout = request_timeout
        else:
            timeout_env = os.getenv("SPAPS_REQUEST_TIMEOUT")
            self.request_timeout = float(timeout_env) if timeout_env else DEFAULT_TIMEOUT


def create_http_client(
    *,
    settings: Settings,
    retry_config: Optional[RetryConfig] = None,
    logging_hooks: Optional[LoggingHooks] = None,
    **kwargs,
) -> httpx.Client:
    """
    Create a configured httpx.Client using the provided settings.

    Extra keyword arguments are forwarded to the httpx.Client constructor.
    """

    timeout = kwargs.pop("timeout", settings.request_timeout)
    client = RetryClient(
        base_url=settings.base_url.rstrip("/"),
        timeout=timeout,
        retry_config=retry_config,
        logging_hooks=logging_hooks,
        **kwargs,
    )
    return client
