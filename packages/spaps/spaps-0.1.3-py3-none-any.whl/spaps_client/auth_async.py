"""
Async authentication client mirroring the synchronous AuthClient API.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx

from .auth import (
    AuthError,
    NonceResponse,
    TokenPair,
    RegistrationResponse,
    MagicLinkSendResponse,
    MagicLinkAuthResponse,
    RegistrationTokens,
    UserProfile,
    PasswordResetRequestResponse,
    MessageResponse,
)
from .storage import StoredTokens, TokenStorage


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


class AsyncAuthClient:
    AUTH_PREFIX = "/api/auth"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        client: Optional[httpx.AsyncClient] = None,
        request_timeout: float | httpx.Timeout = 10.0,
        token_storage: Optional[TokenStorage] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = client or httpx.AsyncClient(base_url=self.base_url, timeout=request_timeout)
        self._owns_client = client is None
        self._token_storage = token_storage

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def request_nonce(self, *, wallet_address: str, chain: Optional[str] = None) -> NonceResponse:
        payload: Dict[str, Any] = {"wallet_address": wallet_address}
        if chain:
            payload["chain"] = chain
        data = await self._post("/nonce", json=payload)
        return NonceResponse.model_validate(data)

    async def verify_wallet(
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
        data = await self._post("/wallet-sign-in", json=payload)
        return self._store_token_pair(TokenPair.model_validate(data))

    async def sign_in_with_password(self, *, email: str, password: str) -> TokenPair:
        payload = {"email": email, "password": password}
        data = await self._post("/login", json=payload)
        return self._store_token_pair(TokenPair.model_validate(data))

    async def refresh_tokens(self, *, refresh_token: str) -> TokenPair:
        payload = {"refresh_token": refresh_token}
        data = await self._post("/refresh", json=payload)
        return self._store_token_pair(TokenPair.model_validate(data))

    async def register(
        self,
        *,
        email: str,
        password: str,
        username: Optional[str] = None,
        phone_number: Optional[str] = None,
    ) -> RegistrationResponse:
        payload: Dict[str, Any] = {"email": email, "password": password}
        if username is not None:
            payload["username"] = username
        if phone_number is not None:
            payload["phone_number"] = phone_number

        raw = await self._post_full("/register", json=payload)
        user_section = raw.get("user")
        data_section = _as_dict(raw.get("data"))
        if user_section is None:
            user_section = data_section.get("user")
        if user_section is None:
            raise AuthError("Registration response missing user payload", status_code=500)

        response_data: Dict[str, Any] = {
            "message": raw.get("message"),
            "user": user_section,
        }
        tokens_section = raw.get("tokens")
        if isinstance(tokens_section, dict):
            response_data["tokens"] = tokens_section

        result = RegistrationResponse.model_validate(response_data)
        if result.tokens is not None:
            self._store_registration_tokens(result.tokens)
        return result

    async def send_magic_link(self, *, email: str) -> MagicLinkSendResponse:
        payload = {"email": email}
        raw = await self._post_full("/magic-link", json=payload)
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

    async def verify_magic_link(self, *, token: str, type: str = "magiclink") -> MagicLinkAuthResponse:
        payload = {"token": token, "type": type}
        raw = await self._post_full("/verify-magic-link", json=payload)
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
        result = MagicLinkAuthResponse.model_validate(response_data)
        if result.tokens is not None:
            self._store_registration_tokens(result.tokens)
        return result

    async def request_password_reset(
        self,
        *,
        email: str,
        redirect_url: Optional[str] = None,
    ) -> PasswordResetRequestResponse:
        payload: Dict[str, Any] = {"email": email}
        if redirect_url is not None:
            payload["redirect_url"] = redirect_url

        raw = await self._post_full("/password-reset", json=payload)
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

    async def confirm_password_reset(
        self,
        *,
        token: str,
        new_password: str,
    ) -> MessageResponse:
        payload = {"token": token, "new_password": new_password}
        raw = await self._post_full("/reset-password-confirm", json=payload)
        message = raw.get("message")
        if not message:
            raise AuthError("Password reset confirmation response missing message", status_code=500)
        return MessageResponse.model_validate({"message": message})

    async def get_current_user(self, *, access_token: Optional[str] = None) -> UserProfile:
        token = self._resolve_access_token(access_token)
        if not token:
            raise ValueError("Access token is required to fetch the current user profile")

        response = await self._client.get(
            f"{self.AUTH_PREFIX}/user",
            headers=self._build_authenticated_headers(token),
        )
        if response.status_code >= 400:
            raise await self._build_error(response)

        payload = response.json()
        user_section = _as_dict(payload.get("data")).get("user", payload.get("user"))
        if not isinstance(user_section, dict):
            raise AuthError(
                "User profile response missing user payload",
                status_code=500,
                response=response,
            )

        return UserProfile.model_validate(user_section)

    async def logout(self, *, access_token: Optional[str] = None) -> None:
        token = self._resolve_access_token(access_token)
        if not token:
            raise ValueError("Access token is required for logout")
        response = await self._client.post(
            f"{self.AUTH_PREFIX}/logout",
            headers=self._build_authenticated_headers(token),
        )
        if response.status_code >= 400:
            raise await self._build_error(response)
        if self._token_storage:
            self._token_storage.clear()

    # ------------------------------------------------------------------
    # Helpers

    def get_stored_tokens(self) -> Optional[StoredTokens]:
        return self._token_storage.load() if self._token_storage else None

    def clear_stored_tokens(self) -> None:
        if self._token_storage:
            self._token_storage.clear()

    def _resolve_access_token(self, override: Optional[str]) -> Optional[str]:
        if override:
            return override
        if self._token_storage:
            stored = self._token_storage.load()
            if stored:
                return stored.access_token
        return None

    def _build_authenticated_headers(self, token: str) -> Dict[str, str]:
        return {"X-API-Key": self.api_key, "Authorization": f"Bearer {token}"}

    async def _post(self, path: str, *, json: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"X-API-Key": self.api_key}
        response = await self._client.post(f"{self.AUTH_PREFIX}{path}", json=json, headers=headers)
        if response.status_code >= 400:
            raise await self._build_error(response)
        payload = response.json()
        return payload.get("data", payload)

    async def _post_full(self, path: str, *, json: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"X-API-Key": self.api_key}
        response = await self._client.post(f"{self.AUTH_PREFIX}{path}", json=json, headers=headers)
        if response.status_code >= 400:
            raise await self._build_error(response)
        return response.json()

    async def _build_error(self, response: httpx.Response) -> AuthError:
        try:
            payload = response.json()
        except ValueError:
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


__all__ = ["AsyncAuthClient"]
