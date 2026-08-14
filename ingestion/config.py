"""Settings the ingest job needs on top of the shared ones."""
from pathlib import Path

from pydantic import SecretStr

from common import config
from common.config import Settings


class IngestSettings(Settings):
    # Optional, unlike the api's. Without it figure description is skipped and
    # the run still succeeds — charts simply stay unsearchable, which is the
    # behaviour before descriptions existed.
    anthropic_api_key: SecretStr | None = None
    # Its own setting rather than the api's `anthropic_model`: describing a
    # chart and triaging a question are different jobs, and this one may need a
    # stronger model without changing what serves requests.
    describe_model: str = "claude-haiku-4-5"
    describe_max_tokens: int = 1024
    # Keyed by image hash, so re-ingestion and `--force` re-describe nothing.
    # Must be writable: the corpus mount is read-only in the container.
    description_cache: Path = Path("logs/common/figure-descriptions.json")

    # Ingestion root, walked recursively. Deliberately the initial set rather
    # than all of `corpus/`: the later batch is copied in to demonstrate
    # incremental ingestion, and the golden answer key stays outside the tree.
    corpus_dir: Path = Path("corpus/docs-initial")

    # Chunks are sized in the embedder's own tokens — see `embedding_model` on
    # the base class. A chunk sized in someone else's tokens overflows silently
    # at embed time.
    chunk_max_tokens: int = 512


def get_settings() -> IngestSettings:
    """The injected settings, narrowed to the ingest job's type."""
    settings = config.get_settings()
    if not isinstance(settings, IngestSettings):
        raise config.ConfigNotSet(
            f"ingestion needs IngestSettings, but {type(settings).__name__} was configured"
        )
    return settings
