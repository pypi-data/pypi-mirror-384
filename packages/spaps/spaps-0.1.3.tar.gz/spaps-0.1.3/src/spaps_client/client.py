"""High-level client aggregating SPAPS service helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, TYPE_CHECKING

import httpx

from .auth import AuthClient
from .config import Settings, create_http_client
from .metrics import MetricsClient
from .payments import PaymentsClient
from .sessions import SessionsClient
from .secure_messages import SecureMessagesClient
from .storage import InMemoryTokenStorage, StoredTokens, TokenStorage
from .usage import UsageClient
from .whitelist import WhitelistClient

if TYPE_CHECKING:
    from .http import RetryConfig, LoggingHooks


class SpapsClient:
    """Convenience wrapper that mirrors the TypeScript SDK ergonomics."""

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        request_timeout: Optional[float] = None,
        token_storage: Optional[TokenStorage] = None,
        http_client: Optional[httpx.Client] = None,
        retry_config: Optional["RetryConfig"] = None,
        logging_hooks: Optional["LoggingHooks"] = None,
    ) -> None:
        from .http import LoggingHooks as _LoggingHooks, RetryConfig as _RetryConfig  # avoid circular import hints

        self.settings = Settings(base_url=base_url, api_key=api_key, request_timeout=request_timeout)
        if isinstance(retry_config, dict):  # allow kwargs-like dict
            retry_config = _RetryConfig(**retry_config)
        if isinstance(logging_hooks, dict):
            logging_hooks = _LoggingHooks(**logging_hooks)

        self._client = http_client or create_http_client(
            settings=self.settings,
            retry_config=retry_config,
            logging_hooks=logging_hooks,
        )
        self._owns_client = http_client is None
        self._token_storage = token_storage or InMemoryTokenStorage()

        self._auth = AuthClient(
            base_url=self.settings.base_url,
            api_key=self.settings.api_key,
            client=self._client,
            token_storage=self._token_storage,
        )

        self._sessions: Optional[SessionsClient] = None
        self._payments: Optional[PaymentsClient] = None
        self._usage: Optional[UsageClient] = None
        self._whitelist: Optional[WhitelistClient] = None
        self._secure_messages: Optional[SecureMessagesClient] = None
        self._metrics: Optional[MetricsClient] = None

    # ------------------------------------------------------------------
    # Client accessors

    @property
    def auth(self) -> AuthClient:
        return self._auth

    @property
    def sessions(self) -> SessionsClient:
        access_token = self._require_access_token()
        if self._sessions is None:
            self._sessions = SessionsClient(
                base_url=self.settings.base_url,
                api_key=self.settings.api_key,
                access_token=access_token,
                client=self._client,
            )
        else:
            self._sessions.access_token = access_token
        return self._sessions

    @property
    def payments(self) -> PaymentsClient:
        access_token = self._require_access_token()
        if self._payments is None:
            self._payments = PaymentsClient(
                base_url=self.settings.base_url,
                api_key=self.settings.api_key,
                access_token=access_token,
                client=self._client,
            )
        else:
            self._payments.access_token = access_token
        return self._payments

    @property
    def usage(self) -> UsageClient:
        access_token = self._require_access_token()
        if self._usage is None:
            self._usage = UsageClient(
                base_url=self.settings.base_url,
                api_key=self.settings.api_key,
                access_token=access_token,
                client=self._client,
            )
        else:
            self._usage.access_token = access_token
        return self._usage

    @property
    def whitelist(self) -> WhitelistClient:
        access_token = self._require_access_token()
        if self._whitelist is None:
            self._whitelist = WhitelistClient(
                base_url=self.settings.base_url,
                api_key=self.settings.api_key,
                access_token=access_token,
                client=self._client,
            )
        else:
            self._whitelist.access_token = access_token
        return self._whitelist

    @property
    def secure_messages(self) -> SecureMessagesClient:
        access_token = self._require_access_token()
        if self._secure_messages is None:
            self._secure_messages = SecureMessagesClient(
                base_url=self.settings.base_url,
                api_key=self.settings.api_key,
                access_token=access_token,
                client=self._client,
            )
        else:
            self._secure_messages.access_token = access_token
        return self._secure_messages

    @property
    def metrics(self) -> MetricsClient:
        if self._metrics is None:
            self._metrics = MetricsClient(base_url=self.settings.base_url, client=self._client)
        return self._metrics

    # ------------------------------------------------------------------
    # Token helpers

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

    # ------------------------------------------------------------------
    # Lifecycle

    def close(self) -> None:
        self._auth.close()
        for candidate in (
            self._sessions,
            self._payments,
            self._usage,
            self._whitelist,
            self._secure_messages,
            self._metrics,
        ):
            if candidate is not None:
                candidate.close()
        if self._owns_client:
            self._client.close()

    # ------------------------------------------------------------------
    # Internal helpers

    def _require_access_token(self) -> str:
        tokens = self._token_storage.load()
        if not tokens or not tokens.access_token:
            raise ValueError(
                "Access token not found. Authenticate via auth helpers or call set_tokens()."
            )
        return tokens.access_token


__all__ = ["SpapsClient"]
