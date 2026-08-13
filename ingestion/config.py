"""Settings the ingest job needs on top of the shared ones."""
from pathlib import Path

from common import config
from common.config import Settings


class IngestSettings(Settings):
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
