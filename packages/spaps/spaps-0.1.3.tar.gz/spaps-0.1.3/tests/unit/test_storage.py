from datetime import datetime, timezone
from pathlib import Path

from spaps_client.storage import FileTokenStorage, InMemoryTokenStorage, StoredTokens


def test_in_memory_storage_round_trip() -> None:
    storage = InMemoryTokenStorage()
    assert storage.load() is None

    tokens = StoredTokens(access_token="access", refresh_token="refresh")
    storage.save(tokens)

    loaded = storage.load()
    assert loaded == tokens

    storage.clear()
    assert storage.load() is None


def test_file_storage_round_trip(tmp_path: Path) -> None:
    storage_path = tmp_path / "tokens.json"
    storage = FileTokenStorage(path=storage_path)
    assert storage.load() is None

    expires_at = datetime.now(timezone.utc)
    storage.save(StoredTokens(access_token="access", refresh_token="refresh", expires_at=expires_at, token_type="Bearer"))

    assert storage_path.exists()
    loaded = storage.load()
    assert loaded is not None
    assert loaded.access_token == "access"
    assert loaded.refresh_token == "refresh"
    assert loaded.token_type == "Bearer"
    assert loaded.expires_at is not None

    storage.clear()
    assert storage.load() is None
    assert not storage_path.exists()
