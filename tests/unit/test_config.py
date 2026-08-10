import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """`get_settings` is cached, so env changes need the cache dropped."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_settings_read_api_key_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-env")

    assert get_settings().anthropic_api_key.get_secret_value() == "sk-ant-from-env"


def test_settings_are_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-first")
    first = get_settings()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-second")

    assert get_settings() is first


def test_missing_api_key_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(ValidationError):
        Settings()


def test_api_key_is_not_exposed_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-super-secret")

    assert "sk-ant-super-secret" not in repr(get_settings())


def test_optional_settings_have_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-env")
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    monkeypatch.delenv("QDRANT_URL", raising=False)
    settings = get_settings()

    assert settings.anthropic_model == "claude-haiku-4-5"
    assert settings.qdrant_url == "http://localhost:6333"
