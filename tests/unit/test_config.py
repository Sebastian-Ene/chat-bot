"""Settings: the shared base, the two children, and the injection slot.

`common/` owns no settings instance — an entrypoint injects a child. These
tests build the classes directly rather than going through the autouse fixture,
because what is under test *is* the construction.
"""
import pytest
from pydantic import ValidationError

from api.core.config import ApiSettings
from api.core.config import get_settings as get_api_settings
from common.config import ConfigNotSet, Settings, configure, get_settings, reset
from ingestion.config import IngestSettings
from ingestion.config import get_settings as get_ingest_settings


class TestBaseSettings:
    def test_qdrant_url_is_required(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Where the database lives is a property of the environment, so there
        is deliberately no default to fall back to."""
        monkeypatch.delenv("QDRANT_URL", raising=False)

        with pytest.raises(ValidationError):
            Settings()

    def test_qdrant_url_is_read_from_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("QDRANT_URL", "http://qdrant:6333")

        assert Settings().qdrant_url == "http://qdrant:6333"

    def test_shared_settings_have_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("QDRANT_URL", "http://localhost:6333")
        monkeypatch.delenv("QDRANT_COLLECTION", raising=False)

        settings = Settings()

        assert settings.qdrant_collection == "chunks"
        assert settings.embedding_model == "BAAI/bge-m3"
        assert settings.embedding_dimensions == 1024

    def test_the_base_carries_no_secrets(self) -> None:
        """The whole point of the split: the ingest job must not have to supply
        an Anthropic key or a JWT secret it never reads."""
        assert "anthropic_api_key" not in Settings.model_fields
        assert "jwt_secret" not in Settings.model_fields


class TestApiSettings:
    def test_reads_the_api_key_from_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-env")

        assert ApiSettings().anthropic_api_key.get_secret_value() == "sk-ant-from-env"

    def test_missing_api_key_is_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ValidationError):
            ApiSettings()

    def test_missing_jwt_secret_is_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("JWT_SECRET", raising=False)

        with pytest.raises(ValidationError):
            ApiSettings()

    def test_api_key_is_not_exposed_in_repr(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-super-secret")

        assert "sk-ant-super-secret" not in repr(ApiSettings())

    def test_inherits_the_shared_settings(self) -> None:
        assert ApiSettings().qdrant_collection == "chunks"


class TestIngestSettings:
    def test_needs_no_secrets(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The ingest job reads neither, and used to fail to start without
        them — which is why both Dockerfiles carried placeholder credentials."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("JWT_SECRET", raising=False)

        settings = IngestSettings()

        assert settings.corpus_dir.name == "docs-initial"
        assert settings.chunk_max_tokens == 512

    def test_inherits_the_shared_settings(self) -> None:
        assert IngestSettings().embedding_model == "BAAI/bge-m3"


class TestInjection:
    def test_reading_before_configuring_raises(self) -> None:
        """A wiring bug, not something to paper over with a default."""
        reset()
        try:
            with pytest.raises(ConfigNotSet):
                get_settings()
        finally:
            # Restore before leaving: fixtures scoped above `function` are set
            # up between tests and would read the empty slot.
            configure(ApiSettings())

    def test_configure_installs_the_child(self) -> None:
        settings = configure(ApiSettings())

        assert get_settings() is settings

    def test_the_narrowed_accessors_return_the_same_instance(self) -> None:
        settings = configure(ApiSettings())

        assert get_api_settings() is settings

    def test_the_wrong_child_is_rejected(self) -> None:
        """`ingestion/` asking for settings in an api process is a wiring bug
        too — the fields it wants would not be there."""
        configure(ApiSettings())

        with pytest.raises(ConfigNotSet):
            get_ingest_settings()
