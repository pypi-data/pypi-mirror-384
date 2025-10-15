"""
Token storage abstractions for the SPAPS Python client.

Provides simple in-memory and file-backed implementations so authentication
tokens can persist across client instances and processes.
"""

from __future__ import annotations

import json
import os
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

__all__ = [
    "StoredTokens",
    "TokenStorage",
    "InMemoryTokenStorage",
    "FileTokenStorage",
]


@dataclass
class StoredTokens:
    """
    Structured representation of persisted authentication tokens.

    Attributes:
        access_token: Bearer token used for authenticated requests.
        refresh_token: Refresh token for obtaining new access tokens.
        expires_at: ISO8601 timestamp indicating when the access token expires.
        token_type: Token type (typically \"Bearer\").
    """

    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    token_type: Optional[str] = None


class TokenStorage(ABC):
    """Abstract base class for storage implementations."""

    @abstractmethod
    def save(self, tokens: StoredTokens) -> None:
        """Persist the provided tokens."""

    @abstractmethod
    def load(self) -> Optional[StoredTokens]:
        """Retrieve the most recently stored tokens, if any."""

    @abstractmethod
    def clear(self) -> None:
        """Remove any persisted tokens."""


class InMemoryTokenStorage(TokenStorage):
    """Simple storage that keeps tokens in memory for the lifetime of the process."""

    def __init__(self) -> None:
        self._tokens: Optional[StoredTokens] = None
        self._lock = threading.Lock()

    def save(self, tokens: StoredTokens) -> None:
        with self._lock:
            self._tokens = tokens

    def load(self) -> Optional[StoredTokens]:
        with self._lock:
            return self._tokens

    def clear(self) -> None:
        with self._lock:
            self._tokens = None


class FileTokenStorage(TokenStorage):
    """
    File-backed storage that persists tokens between executions.

    Tokens are stored in JSON format with restrictive permissions to mitigate
    accidental exposure.
    """

    def __init__(self, *, path: Optional[Path | str] = None) -> None:
        if path is None:
            path = Path.home() / ".config" / "spaps" / "tokens.json"
        self._path = Path(path).expanduser()
        self._lock = threading.Lock()
        self._ensure_parent_directory()

    def _ensure_parent_directory(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, tokens: StoredTokens) -> None:
        payload = {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "expires_at": tokens.expires_at.isoformat() if tokens.expires_at else None,
            "token_type": tokens.token_type,
        }
        serialized = json.dumps(payload, indent=2)
        with self._lock:
            self._ensure_parent_directory()
            self._path.write_text(serialized, encoding="utf-8")
            try:
                os.chmod(self._path, 0o600)
            except OSError:
                # Best-effort; ignore on platforms that do not support chmod.
                pass

    def load(self) -> Optional[StoredTokens]:
        with self._lock:
            if not self._path.exists():
                return None
            try:
                payload = json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return None
        expires_at_raw = payload.get("expires_at")
        expires_at: Optional[datetime] = None
        if isinstance(expires_at_raw, str):
            try:
                expires_at = datetime.fromisoformat(expires_at_raw)
            except ValueError:
                expires_at = None
        return StoredTokens(
            access_token=payload.get("access_token", ""),
            refresh_token=payload.get("refresh_token"),
            expires_at=expires_at,
            token_type=payload.get("token_type"),
        )

    def clear(self) -> None:
        with self._lock:
            if self._path.exists():
                try:
                    self._path.unlink()
                except OSError:
                    # Ignore failures to delete; caller can decide how to handle.
                    pass
