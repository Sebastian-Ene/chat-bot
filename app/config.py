from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# `.env` is loaded into the OS environment; values already present there win,
# so real deployments can configure the app without shipping a file.
load_dotenv()


class Settings(BaseSettings):
    """Application configuration, read from the OS environment.

    The single place model and service configuration lives — secrets are never
    hardcoded in source (requirements.md §6.3, §7.3).
    """

    model_config = SettingsConfigDict(extra="ignore")

    anthropic_api_key: SecretStr
    anthropic_model: str = "claude-haiku-4-5"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "chunks"

    # One secret for the whole app, supplied via `.env`. Every process that
    # serves the app must share it, or tokens minted by one are rejected by
    # another.
    jwt_secret: SecretStr
    jwt_ttl_seconds: int = 300

    # Extra retrieval branches from the rewrite. Both are unproven — switch them
    # off to A/B against the eval harness once a corpus exists.
    rewrite_keywords_enabled: bool = True
    rewrite_sub_queries_enabled: bool = True

    # Ingestion root, walked recursively. Deliberately the initial set rather
    # than all of `corpus/`: the later batch is copied in to demonstrate
    # incremental ingestion, and the golden answer key stays outside the tree.
    corpus_dir: Path = Path("corpus/docs-initial")

    # One model for both index-time and query-time embedding — they must never
    # drift, so this setting feeds the chunker's tokenizer and the embedder
    # alike. Chunks are sized in BGE-M3's own tokens; 512 rather than its 8192
    # ceiling, because a large chunk dilutes the embedding and costs precision.
    embedding_model: str = "BAAI/bge-m3"
    chunk_max_tokens: int = 512

    # DEBUG by default: per-stage timings are only measured at this level, and
    # this is a PoC whose latency breakdown is a deliverable.
    log_level: str = "DEBUG"
    log_dir: Path = Path("logs")
    # Caps the message/prompt/chunk text in DEBUG trace lines. Prompts are tiny
    # today; with real retrieved chunks they would swamp the log.
    log_max_chars: int = 2000


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings, built once on first use."""
    return Settings()
