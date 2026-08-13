"""Qdrant client, the startup connectivity check, and the collection schema.

The check **fails the app's startup** if Qdrant cannot be reached. Docker
Compose is the supported way to run this project, and there the database is a
declared dependency — an api that boots without its vector store would only
fail later, per request, with a worse error. Running outside Compose means
providing Qdrant yourself.

The collection is created by the ingest job, never by the api: the api only
reads, and a reader that quietly creates an empty collection would turn "the
corpus was never ingested" into "every question is unanswerable" — much harder
to diagnose.

Note this module is imported by the api, so it must not import
`common.embedding` — that would pull FlagEmbedding and torch into the api image,
which deliberately carries neither. Hence the vector width comes from settings.
"""
import logging

from qdrant_client import QdrantClient, models

from common.config import get_settings
from common.logging_config import APP_LOGGER

logger = logging.getLogger(APP_LOGGER)

# Named vectors: one point carries both, so a hybrid query prefetches each
# branch and fuses server-side rather than hitting two collections.
DENSE_VECTOR = "dense"
SPARSE_VECTOR = "sparse"

# Dot product, NOT cosine — a deliberate choice that depends on an invariant.
#
# BGE-M3 is loaded with `normalize_embeddings=True`, and for unit-norm vectors
# dot and cosine are identical, so this costs nothing and skips Qdrant's
# normalisation pass at upsert.
#
# The catch: if embeddings ever stop being normalised — the setting flipped, a
# different model, a hand-inserted point — dot becomes silently wrong rather
# than erroring. Longer chunks carry larger norms and would rank higher
# regardless of relevance, with nothing in any log. `tests/ingest/
# test_embedding_model.py` asserts unit norm to keep that honest. Changing the
# embedding setup means revisiting this line.
DENSE_DISTANCE = models.Distance.DOT

_client: QdrantClient | None = None


class VectorStoreUnavailable(RuntimeError):
    """Qdrant could not be reached at startup."""


class CollectionMismatch(RuntimeError):
    """The existing collection does not match the configured embedding."""


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


def _check_matches_configuration(client: QdrantClient, collection: str) -> None:
    """Refuse to write into a collection built for a different embedding.

    This fires the moment someone changes `embedding_model` without rebuilding
    the index. Without it, new points land beside incompatible old ones and the
    only symptom is retrieval quietly getting worse.
    """
    settings = get_settings()
    info = client.get_collection(collection)
    dense = info.config.params.vectors.get(DENSE_VECTOR)

    if dense is None:
        raise CollectionMismatch(
            f"collection '{collection}' has no '{DENSE_VECTOR}' vector — it was "
            "built by an older schema. Delete it and re-run ingestion."
        )
    if dense.size != settings.embedding_dimensions:
        raise CollectionMismatch(
            f"collection '{collection}' holds {dense.size}-d vectors but "
            f"{settings.embedding_model} produces {settings.embedding_dimensions}. "
            "Delete the collection and re-run ingestion."
        )
    if dense.distance != DENSE_DISTANCE:
        raise CollectionMismatch(
            f"collection '{collection}' uses {dense.distance} but this build "
            f"expects {DENSE_DISTANCE}. Delete the collection and re-run ingestion."
        )


def ensure_collection(client: QdrantClient, collection: str | None = None) -> None:
    """Create the collection if absent; verify it matches if present.

    Called by the ingest job only — see the module docstring.
    """
    settings = get_settings()
    collection = collection or settings.qdrant_collection

    if client.collection_exists(collection):
        _check_matches_configuration(client, collection)
        logger.debug("collection '%s' already present", collection)
        return

    client.create_collection(
        collection_name=collection,
        vectors_config={
            DENSE_VECTOR: models.VectorParams(
                size=settings.embedding_dimensions, distance=DENSE_DISTANCE
            )
        },
        sparse_vectors_config={SPARSE_VECTOR: models.SparseVectorParams()},
    )
    # Every state read and every delete filters on doc_id; without an index
    # Qdrant scans the whole collection for each one.
    client.create_payload_index(
        collection_name=collection,
        field_name="doc_id",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    logger.info(
        "created collection '%s' dense=%dd/%s sparse=%s",
        collection,
        settings.embedding_dimensions,
        DENSE_DISTANCE,
        SPARSE_VECTOR,
    )
