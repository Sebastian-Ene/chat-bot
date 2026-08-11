"""Qdrant client and the startup connectivity check.

The check **fails the app's startup** if Qdrant cannot be reached. Docker
Compose is the supported way to run this project, and there the database is a
declared dependency — an api that boots without its vector store would only
fail later, per request, with a worse error. Running outside Compose means
providing Qdrant yourself.
"""
import logging

from qdrant_client import QdrantClient

from app.config import get_settings
from app.logging_config import APP_LOGGER

logger = logging.getLogger(APP_LOGGER)

_client: QdrantClient | None = None


class VectorStoreUnavailable(RuntimeError):
    """Qdrant could not be reached at startup."""


def get_client() -> QdrantClient:
    """One client for the process, created on first use."""
    global _client
    if _client is None:
        _client = QdrantClient(url=get_settings().qdrant_url)
    return _client


def check_connection() -> list[str]:
    """Verify Qdrant answers, returning the collection names it reports."""
    url = get_settings().qdrant_url
    try:
        collections = [c.name for c in get_client().get_collections().collections]
    except Exception as error:
        raise VectorStoreUnavailable(
            f"Qdrant unreachable at {url}: {type(error).__name__}: {error}. "
            "Run the project with `docker compose up`, or provide Qdrant yourself."
        ) from error

    logger.info("qdrant connected url=%s collections=%s", url, collections or "none")
    return collections
