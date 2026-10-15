import pytest

from app import config
from app.config import Settings


def test_settings_use_numeric_defaults_without_requiring_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    for name in ("BASE_URL", "API_KEY", "TIMEOUT", "MAX_RETRIES", "BACKOFF_FACTOR"):
        monkeypatch.delenv(name, raising=False)

    monkeypatch.setenv("BASE_URL", "https://api.example.test")
    settings = Settings.from_environment()

    assert settings.base_url == "https://api.example.test"
    assert settings.api_key is None
    assert settings.timeout == 15
    assert settings.max_retries == 3


def test_settings_require_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    monkeypatch.delenv("BASE_URL", raising=False)

    with pytest.raises(ValueError, match="BASE_URL is required"):
        Settings.from_environment()


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("BASE_URL", "not-a-url", "BASE_URL"),
        ("TIMEOUT", "abc", "must be numbers"),
        ("TIMEOUT", "0", "greater than zero"),
        ("MAX_RETRIES", "-1", "cannot be negative"),
        ("BACKOFF_FACTOR", "-0.1", "cannot be negative"),
    ],
)
def test_settings_reject_invalid_values(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
    message: str,
) -> None:
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    monkeypatch.setenv("BASE_URL", "https://api.example.test")
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError, match=message):
        Settings.from_environment()
