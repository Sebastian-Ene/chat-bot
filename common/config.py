"""Settings shared by the api and the ingest job, and the slot they inject into.

`common/` deliberately owns **no** settings instance of its own. Each entrypoint
builds its own `Settings` subclass — `ApiSettings` or `IngestSettings` — and
hands it to `configure()` before anything else runs. Modules here then read that
instance through `get_settings()`, so the shared code sees whichever child the
running process supplied.

Anything only one side needs belongs on that side's subclass, not here: the
ingester should not have to supply an Anthropic key it never uses.
"""
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# `.env` is loaded into the OS environment; values already present there win,
# so real deployments can configure the app without shipping a file.
load_dotenv()


class Settings(BaseSettings):
    """Configuration both the api and the ingest job need.

    Read from the OS environment — secrets are never hardcoded in source
    (requirements.md §6.3, §7.3).
    """

    model_config = SettingsConfigDict(extra="ignore")

    # Required, with no default: where Qdrant lives is a property of the
    # environment, not of the code. Compose supplies the service name; a local
    # run supplies localhost via `.env`.
    qdrant_url: str
    qdrant_collection: str = "chunks"

    # One model for both index-time and query-time embedding — they must never
    # drift, so this setting feeds the chunker's tokenizer and the embedder
    # alike. Chunks are sized in BGE-M3's own tokens; 512 rather than its 8192
    # ceiling, because a large chunk dilutes the embedding and costs precision.
    embedding_model: str = "BAAI/bge-m3"
    # BGE-M3's dense width. Lives here rather than in `common/embedding.py` because
    # the collection schema needs it and the api must be able to read it without
    # importing the embedding stack — that would drag torch into the api image.
    embedding_dimensions: int = 1024
    embed_max_tokens: int = 1024
    embed_batch_size: int = 16

    # DEBUG by default: per-stage timings are only measured at this level, and
    # this is a PoC whose latency breakdown is a deliverable.
    log_level: str = "DEBUG"
    log_dir: Path = Path("logs")
    # Caps the message/prompt/chunk text in DEBUG trace lines. Prompts are tiny
    # today; with real retrieved chunks they would swamp the log.
    log_max_chars: int = 2000


class ConfigNotSet(RuntimeError):
    """`get_settings()` was called before an entrypoint injected the settings."""


_settings: Settings | None = None


def configure(settings: Settings) -> Settings:
    """Install the process-wide settings. Call once, first thing at startup."""
    global _settings
    _settings = settings
    return settings


def get_settings() -> Settings:
    """The injected settings — an `ApiSettings` or an `IngestSettings`.

    Raises rather than building a default: a module reading configuration
    before the entrypoint set it is a wiring bug, and silently inventing
    settings would hide it until something behaved oddly in production.
    """
    if _settings is None:
        raise ConfigNotSet(
            "settings were never configured — an entrypoint must call "
            "common.config.configure() before anything reads configuration"
        )
    return _settings


def reset() -> None:
    """Drop the injected settings. For tests, which reconfigure per case."""
    global _settings
    _settings = None
