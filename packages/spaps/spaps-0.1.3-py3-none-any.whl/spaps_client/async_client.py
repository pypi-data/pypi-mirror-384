"""Async equivalents for the SPAPS client suite."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, TYPE_CHECKING

import httpx

from .auth_async import AsyncAuthClient
from .sessions_async import AsyncSessionsClient
from .payments_async import AsyncPaymentsClient
from .usage_async import AsyncUsageClient
from .whitelist_async import AsyncWhitelistClient
from .secure_messages_async import AsyncSecureMessagesClient
from .metrics_async import AsyncMetricsClient
from .storage import InMemoryTokenStorage, StoredTokens, TokenStorage
from .config import Settings

if TYPE_CHECKING:
    from .http import RetryConfig, LoggingHooks


class AsyncSpapsClient:
    """Async client mirroring the ergonomics of the synchronous variant."""

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        request_timeout: Optional[float] = None,
        token_storage: Optional[TokenStorage] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        retry_config: Optional["RetryConfig"] = None,
        logging_hooks: Optional["LoggingHooks"] = None,
    ) -> None:
        from .http_async import RetryAsyncClient

        self.settings = Settings(base_url=base_url, api_key=api_key, request_timeout=request_timeout)
        self._token_storage = token_storage or InMemoryTokenStorage()
        from .http import RetryConfig as _RetryConfig, LoggingHooks as _LoggingHooks
        if isinstance(retry_config, dict):
            retry_config = _RetryConfig(**retry_config)
        if isinstance(logging_hooks, dict):
            logging_hooks = _LoggingHooks(**logging_hooks)
        if http_client is not None:
            self._client = http_client
            self._owns_client = False
        else:
            self._client = RetryAsyncClient(
                base_url=self.settings.base_url.rstrip("/"),
                timeout=self.settings.request_timeout,
                retry_config=retry_config,
                logging_hooks=logging_hooks,
            )
            self._owns_client = True

        self._auth = AsyncAuthClient(
            base_url=self.settings.base_url,
            api_key=self.settings.api_key,
            client=self._client,
            token_storage=self._token_storage,
        )

        self._sessions: Optional[AsyncSessionsClient] = None
        self._payments: Optional[AsyncPaymentsClient] = None
        self._usage: Optional[AsyncUsageClient] = None
        self._whitelist: Optional[AsyncWhitelistClient] = None
        self._secure_messages: Optional[AsyncSecureMessagesClient] = None
        self._metrics: Optional[AsyncMetricsClient] = None

    # Factories --------------------------------------------------------

    @property
    def auth(self) -> AsyncAuthClient:
        return self._auth

    @property
    def sessions(self) -> AsyncSessionsClient:
        access_token = self._require_access_token()
        if self._sessions is None:
            self._sessions = AsyncSessionsClient(
                base_url=self.settings.base_url,
                api_key=self.settings.api_key,
                access_token=access_token,
                client=self._client,
            )
        else:
            self._sessions.access_token = access_token
        return self._sessions

    @property
    def payments(self) -> AsyncPaymentsClient:
        access_token = self._require_access_token()
        if self._payments is None:
            self._payments = AsyncPaymentsClient(
                base_url=self.settings.base_url,
                api_key=self.settings.api_key,
                access_token=access_token,
                client=self._client,
            )
        else:
            self._payments.access_token = access_token
        return self._payments

    @property
    def usage(self) -> AsyncUsageClient:
        access_token = self._require_access_token()
        if self._usage is None:
            self._usage = AsyncUsageClient(
                base_url=self.settings.base_url,
                api_key=self.settings.api_key,
                access_token=access_token,
                client=self._client,
            )
        else:
            self._usage.access_token = access_token
        return self._usage

    @property
    def whitelist(self) -> AsyncWhitelistClient:
        access_token = self._require_access_token()
        if self._whitelist is None:
            self._whitelist = AsyncWhitelistClient(
                base_url=self.settings.base_url,
                api_key=self.settings.api_key,
                access_token=access_token,
                client=self._client,
            )
        else:
            self._whitelist.access_token = access_token
        return self._whitelist

    @property
    def secure_messages(self) -> AsyncSecureMessagesClient:
        access_token = self._require_access_token()
        if self._secure_messages is None:
            self._secure_messages = AsyncSecureMessagesClient(
                base_url=self.settings.base_url,
                api_key=self.settings.api_key,
                access_token=access_token,
                client=self._client,
            )
        else:
            self._secure_messages.access_token = access_token
        return self._secure_messages

    @property
    def metrics(self) -> AsyncMetricsClient:
        if self._metrics is None:
            self._metrics = AsyncMetricsClient(base_url=self.settings.base_url, client=self._client)
        return self._metrics

    # Token helpers ----------------------------------------------------

    @property
    def token_storage(self) -> TokenStorage:
        return self._token_storage

    def get_tokens(self) -> Optional[StoredTokens]:
        return self._token_storage.load()

    def set_tokens(
        self,
        *,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_type: Optional[str] = "Bearer",
        expires_in: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> None:
        if expires_at is None and expires_in is not None:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        tokens = StoredTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            token_type=token_type,
        )
        self._token_storage.save(tokens)

    def clear_tokens(self) -> None:
        self._token_storage.clear()

    # Lifecycle --------------------------------------------------------

    async def aclose(self) -> None:
        await self._auth.aclose()
        for candidate in (
            self._sessions,
            self._payments,
            self._usage,
            self._whitelist,
            self._secure_messages,
            self._metrics,
        ):
            if candidate is not None:
                await candidate.aclose()
        if self._owns_client:
            await self._client.aclose()

    # Internal helpers -------------------------------------------------

    def _require_access_token(self) -> str:
        tokens = self._token_storage.load()
        if not tokens or not tokens.access_token:
            raise ValueError(
                "Access token not found. Authenticate via auth helpers or call set_tokens()."
            )
        return tokens.access_token


__all__ = ["AsyncSpapsClient"]
