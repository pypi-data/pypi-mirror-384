"""
Authentication helpers for the Sweet Potato Authentication & Payment Service.

The AuthClient wraps SPAPS authentication endpoints, including wallet-based
nonce generation, signature verification, and refresh token handling.
"""

from __future__ import annotations

import datetime as dt
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel, ConfigDict, Field

from .storage import StoredTokens, TokenStorage

__all__ = [
    "AuthClient",
    "AuthError",
    "NonceResponse",
    "TokenPair",
    "TokenUser",
    "RegistrationTokens",
    "RegistrationUser",
    "RegistrationResponse",
    "MagicLinkSendResponse",
    "MagicLinkAuthResponse",
    "MessageResponse",
    "PasswordResetRequestResponse",
    "UserWallet",
    "UserProfile",
]


class AuthError(Exception):
    """Raised when the SPAPS auth API returns an error response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        error_code: Optional[str] = None,
        response: Optional[httpx.Response] = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.response = response
        self.request_id = request_id


class NonceResponse(BaseModel):
    """Represents the nonce payload returned by `/api/auth/nonce`."""

    model_config = ConfigDict(extra="ignore")

    nonce: str
    message: str
    wallet_address: str
    expires_at: dt.datetime


class TokenUser(BaseModel):
    """User summary returned within auth token responses."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    user_id: str = Field(alias="id")
    wallet_address: Optional[str] = None
    chain: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    wallets: Optional[list[str]] = None
    tier: Optional[str] = None
    email_confirmed: Optional[bool] = None
    phone_number: Optional[str] = None


class TokenPair(BaseModel):
    """Represents an access/refresh token pair."""

    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
    user: TokenUser


class RegistrationTokens(BaseModel):
    model_config = ConfigDict(extra="ignore")

    access_token: str
    refresh_token: str
    expires_in: int


class RegistrationUser(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    email: Optional[str] = None
    username: Optional[str] = None
    email_confirmed: Optional[bool] = None
    phone_number: Optional[str] = None
    tier: Optional[str] = None
    wallets: Optional[list[str]] = None


class RegistrationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: Optional[str] = None
    tokens: Optional[RegistrationTokens] = None
    user: RegistrationUser


class MagicLinkSendResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str
    email: Optional[str] = None
    sent_at: Optional[dt.datetime] = None


class MagicLinkAuthResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: Optional[str] = None
    tokens: Optional[RegistrationTokens] = None
    user: RegistrationUser


class MessageResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str


class PasswordResetRequestResponse(BaseModel):
    """Response payload returned after requesting a password reset."""

    model_config = ConfigDict(extra="ignore")

    message: str
    email: Optional[str] = None
    sent_at: Optional[dt.datetime] = None


class UserWallet(BaseModel):
    """Wallet information associated with a user profile."""

    model_config = ConfigDict(extra="ignore")

    wallet_address: str
    chain_type: Optional[str] = None
    verified: Optional[bool] = None


class UserProfile(BaseModel):
    """Detailed user profile returned by `/api/auth/user`."""

    model_config = ConfigDict(extra="ignore")

    id: str
    username: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    wallets: list[UserWallet] = Field(default_factory=list)
    tier: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


class AuthClient:
    """Client wrapper for SPAPS auth endpoints."""

    AUTH_PREFIX = "/api/auth"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        client: Optional[httpx.Client] = None,
        request_timeout: float | httpx.Timeout = 10.0,
        token_storage: Optional[TokenStorage] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = client or httpx.Client(base_url=self.base_url, timeout=request_timeout)
        self._owns_client = client is None
        self._token_storage = token_storage

    def __enter__(self) -> "AuthClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore[override]
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def get_stored_tokens(self) -> Optional[StoredTokens]:
        """Return tokens stored via the configured token storage, if any."""

        if not self._token_storage:
            return None
        return self._token_storage.load()

    def clear_stored_tokens(self) -> None:
        """Clear any persisted tokens."""

        if self._token_storage:
            self._token_storage.clear()

    # Public API

    def request_nonce(self, *, wallet_address: str, chain: Optional[str] = None) -> NonceResponse:
        payload: Dict[str, Any] = {"wallet_address": wallet_address}
        if chain:
            payload["chain"] = chain

        data = self._post("/nonce", json=payload)
        return NonceResponse.model_validate(data)

    def verify_wallet(
        self,
        *,
        wallet_address: str,
        signature: str,
        message: str,
        chain: Optional[str] = None,
    ) -> TokenPair:
        payload: Dict[str, Any] = {
            "wallet_address": wallet_address,
            "signature": signature,
            "message": message,
        }
        if chain:
            payload["chain_type"] = chain

        data = self._post("/wallet-sign-in", json=payload)
        token_pair = TokenPair.model_validate(data)
        return self._store_token_pair(token_pair)

    def sign_in_with_password(self, *, email: str, password: str) -> TokenPair:
        payload = {"email": email, "password": password}
        data = self._post("/login", json=payload)
        token_pair = TokenPair.model_validate(data)
        return self._store_token_pair(token_pair)

    def refresh_tokens(self, *, refresh_token: str) -> TokenPair:
        payload = {"refresh_token": refresh_token}
        data = self._post("/refresh", json=payload)
        token_pair = TokenPair.model_validate(data)
        return self._store_token_pair(token_pair)

    def register(
        self,
        *,
        email: str,
        password: str,
        username: Optional[str] = None,
        phone_number: Optional[str] = None,
    ) -> RegistrationResponse:
        payload: Dict[str, Any] = {
            "email": email,
            "password": password,
        }
        if username is not None:
            payload["username"] = username
        if phone_number is not None:
            payload["phone_number"] = phone_number

        full_payload = self._post_full("/register", json=payload)
        user_section = full_payload.get("user")
        data_section = _as_dict(full_payload.get("data"))
        if user_section is None:
            user_section = data_section.get("user")

        if user_section is None:
            raise AuthError("Registration response missing user payload", status_code=500)

        response_data: Dict[str, Any] = {
            "message": full_payload.get("message"),
            "user": user_section,
        }
        tokens_section = full_payload.get("tokens")
        if isinstance(tokens_section, dict):
            response_data["tokens"] = tokens_section
        response_model = RegistrationResponse.model_validate(response_data)
        if response_model.tokens is not None:
            self._store_registration_tokens(response_model.tokens)
        return response_model

    def send_magic_link(
        self,
        *,
        email: str,
    ) -> MagicLinkSendResponse:
        payload = {"email": email}
        raw = self._post_full("/magic-link", json=payload)
        data_section = _as_dict(raw.get("data"))
        message = raw.get("message") or data_section.get("message")
        if not message:
            raise AuthError("Magic link response missing message", status_code=500)
        mapped = {
            "message": message,
            "email": data_section.get("email"),
            "sent_at": data_section.get("sent_at"),
        }
        return MagicLinkSendResponse.model_validate(mapped)

    def verify_magic_link(
        self,
        *,
        token: str,
        type: str = "magiclink",
    ) -> MagicLinkAuthResponse:
        payload = {"token": token, "type": type}
        raw = self._post_full("/verify-magic-link", json=payload)
        user_section = raw.get("user")
        if user_section is None:
            raise AuthError("Magic link verification response missing user", status_code=500)
        response_data: Dict[str, Any] = {
            "message": raw.get("message"),
            "user": user_section,
        }
        tokens_section = raw.get("tokens")
        if isinstance(tokens_section, dict):
            response_data["tokens"] = tokens_section
        response_model = MagicLinkAuthResponse.model_validate(response_data)
        if response_model.tokens is not None:
            self._store_registration_tokens(response_model.tokens)
        return response_model

    def get_current_user(self, *, access_token: Optional[str] = None) -> UserProfile:
        """
        Retrieve the authenticated user's profile.

        When ``access_token`` is not supplied, the method falls back to any token
        stored via the configured token storage.
        """

        token = self._resolve_access_token(access_token)
        if not token:
            raise ValueError("Access token is required to fetch the current user profile")

        response = self._client.get(
            f"{self.AUTH_PREFIX}/user",
            headers=self._build_authenticated_headers(token),
        )
        if response.status_code >= 400:
            raise self._build_error(response)

        payload = response.json()
        user_section = _as_dict(payload.get("data")).get("user", payload.get("user"))
        if not isinstance(user_section, dict):
            raise AuthError(
                "User profile response missing user payload",
                status_code=500,
                response=response,
            )

        return UserProfile.model_validate(user_section)

    def logout(self, *, access_token: Optional[str] = None) -> MessageResponse:
        token = self._resolve_access_token(access_token)
        if not token:
            raise ValueError("Access token is required for logout")

        response = self._client.post(
            f"{self.AUTH_PREFIX}/logout",
            headers=self._build_authenticated_headers(token),
        )
        if response.status_code >= 400:
            raise self._build_error(response)
        raw = response.json()
        message = raw.get("data", {}).get("message") or raw.get("message")
        if not message:
            raise AuthError("Logout response missing message", status_code=500, response=response)
        self.clear_stored_tokens()
        return MessageResponse.model_validate({"message": message})

    def request_password_reset(
        self,
        *,
        email: str,
        redirect_url: Optional[str] = None,
    ) -> PasswordResetRequestResponse:
        payload: Dict[str, Any] = {"email": email}
        if redirect_url is not None:
            payload["redirect_url"] = redirect_url

        raw = self._post_full("/password-reset", json=payload)
        data_section = _as_dict(raw.get("data"))
        message = raw.get("message") or data_section.get("message")
        if not message:
            raise AuthError("Password reset response missing message", status_code=500)

        mapped = {
            "message": message,
            "email": data_section.get("email"),
            "sent_at": data_section.get("sent_at"),
        }
        return PasswordResetRequestResponse.model_validate(mapped)

    def confirm_password_reset(
        self,
        *,
        token: str,
        new_password: str,
    ) -> MessageResponse:
        payload = {"token": token, "new_password": new_password}
        raw = self._post_full("/reset-password-confirm", json=payload)
        message = raw.get("message")
        if not message:
            raise AuthError("Password reset confirmation response missing message", status_code=500)
        return MessageResponse.model_validate({"message": message})

    # Internal helpers

    def _resolve_access_token(self, override: Optional[str]) -> Optional[str]:
        if override:
            return override
        stored = self.get_stored_tokens()
        if stored:
            return stored.access_token
        return None

    def _build_authenticated_headers(self, token: str) -> Dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "Authorization": f"Bearer {token}",
        }

    def _post(self, path: str, *, json: Dict[str, Any]) -> Dict[str, Any]:
        headers = {
            "X-API-Key": self.api_key,
        }
        response = self._client.post(f"{self.AUTH_PREFIX}{path}", json=json, headers=headers)
        if response.status_code >= 400:
            raise self._build_error(response)

        payload = response.json()
        # Some endpoints wrap data under "data"; fall back to raw payload.
        return payload.get("data", payload)

    def _post_full(self, path: str, *, json: Dict[str, Any]) -> Dict[str, Any]:
        headers = {
            "X-API-Key": self.api_key,
        }
        response = self._client.post(f"{self.AUTH_PREFIX}{path}", json=json, headers=headers)
        if response.status_code >= 400:
            raise self._build_error(response)
        return response.json()

    @staticmethod
    def _build_error(response: httpx.Response) -> AuthError:
        try:
            payload = response.json()
        except ValueError:  # pragma: no cover - non-JSON responses are unexpected
            payload = {}
        error_info = payload.get("error", {})
        message = error_info.get("message") or response.text or "Authentication request failed"
        request_id = (
            response.headers.get("x-request-id")
            or payload.get("metadata", {}).get("request_id")
        )
        return AuthError(
            message,
            status_code=response.status_code,
            error_code=error_info.get("code"),
            response=response,
            request_id=request_id,
        )

    def _store_token_pair(self, token_pair: TokenPair) -> TokenPair:
        self._store_tokens(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            expires_in=token_pair.expires_in,
            token_type=token_pair.token_type,
        )
        return token_pair

    def _store_registration_tokens(self, tokens: RegistrationTokens) -> None:
        self._store_tokens(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
            token_type="Bearer",
        )

    def _store_tokens(
        self,
        *,
        access_token: str,
        refresh_token: Optional[str],
        expires_in: Optional[int],
        token_type: Optional[str],
    ) -> None:
        if not self._token_storage:
            return
        expires_at: Optional[datetime] = None
        if expires_in is not None:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        self._token_storage.save(
            StoredTokens(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                token_type=token_type,
            )
        )
