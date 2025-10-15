import pytest

from spaps_client import config


@pytest.fixture(autouse=True)
def clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    env_vars = [
        "SPAPS_API_URL",
        "SPAPS_API_KEY",
        "SPAPS_REQUEST_TIMEOUT",
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)


def test_settings_loads_defaults_when_env_missing() -> None:
    settings = config.Settings()
    assert settings.base_url == "http://localhost:3300"
    assert settings.api_key == "test_key_local_dev_only"
    assert settings.request_timeout == 10.0


def test_settings_reads_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPAPS_API_URL", "https://api.sweetpotato.dev")
    monkeypatch.setenv("SPAPS_API_KEY", "live-key")
    monkeypatch.setenv("SPAPS_REQUEST_TIMEOUT", "5.5")

    settings = config.Settings()
    assert settings.base_url == "https://api.sweetpotato.dev"
    assert settings.api_key == "live-key"
    assert settings.request_timeout == pytest.approx(5.5)


def test_settings_accepts_overrides() -> None:
    settings = config.Settings(
        base_url="https://override",
        api_key="override-key",
        request_timeout=2.0,
    )
    assert settings.base_url == "https://override"
    assert settings.api_key == "override-key"
    assert settings.request_timeout == 2.0


def test_http_client_uses_timeout_setting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPAPS_REQUEST_TIMEOUT", "3.0")
    settings = config.Settings()
    client = config.create_http_client(settings=settings)
    assert client.timeout.read == 3.0  # type: ignore[attr-defined]
    client.close()
