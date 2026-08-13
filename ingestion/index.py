"""Writing a document's chunks into Qdrant.

Two invariants live here.

**One upsert per document.** `state.py` reads what is indexed back out of the
collection, so a document must be present at a content hash or absent — never
half-written. Batching points across documents would break that.

**New points first, stale points second.** When a document changes, its new
chunks are upserted before the previous version's are deleted. A crash between
the two leaves duplicates, which are visible in the collection and repaired on
the next run; the reverse order would leave a window where the document has
silently vanished from retrieval.
"""
import logging
import uuid

from qdrant_client import QdrantClient, models

from ingestion.config import get_settings
from common.embedding import Embedding
from common.logging_config import INGEST_LOGGER
from common.vector_store import DENSE_VECTOR, SPARSE_VECTOR
from ingestion.chunk import Chunk

logger = logging.getLogger(INGEST_LOGGER)


def point_id(doc_id: str, chunk_index: int) -> str:
    """A stable id for a chunk, so re-ingesting overwrites rather than duplicates.

    Qdrant takes UUIDs or unsigned ints, not the natural string key, so the key
    is hashed into a UUID.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:{chunk_index}"))


def to_points(
    chunks: list[Chunk], embeddings: list[Embedding]
) -> list[models.PointStruct]:
    """Pair chunks with their vectors.

    The payload carries the chunk text: retrieval then answers in one round
    trip and the generator gets its context directly, rather than the api
    having to mount the corpus and read documents off disk.

    `embed_text` is deliberately not stored — it exists only to be vectorised,
    and keeping it would leave synthetic heading breadcrumbs one careless line
    away from the prompt.
    """
    points = []
    for chunk, embedding in zip(chunks, embeddings, strict=True):
        indices, values = embedding.sparse_indices_and_values()
        points.append(
            models.PointStruct(
                id=point_id(chunk.doc_id, chunk.chunk_index),
                vector={
                    DENSE_VECTOR: embedding.dense,
                    SPARSE_VECTOR: models.SparseVector(indices=indices, values=values),
                },
                payload={
                    "doc_id": chunk.doc_id,
                    "doc_content_hash": chunk.doc_content_hash,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "headings": chunk.headings,
                    "page_numbers": chunk.page_numbers,
                    "source_format": chunk.source_format,
                    "parent_id": chunk.parent_id,
                },
            )
        )
    return points


def index_document(
    client: QdrantClient,
    chunks: list[Chunk],
    embeddings: list[Embedding],
    collection: str | None = None,
) -> int:
    """Write one document's chunks in a single upsert. Returns points written."""
    if not chunks:
        return 0

    collection = collection or get_settings().qdrant_collection
    points = to_points(chunks, embeddings)
    # wait=True: the next step deletes the previous version, and that must not
    # race a write that has not landed yet.
    client.upsert(collection_name=collection, points=points, wait=True)
    logger.debug("indexed %s points=%d", chunks[0].doc_id, len(points))
    return len(points)


def delete_stale(
    client: QdrantClient,
    doc_id: str,
    keep_hash: str,
    collection: str | None = None,
) -> int:
    """Remove points for `doc_id` left over from an earlier version.

    Deterministic ids overwrite chunk-for-chunk, so this only matters when the
    new version has *fewer* chunks than the old — otherwise the tail of the
    previous version would survive as orphaned, unreachable context.
    """
    collection = collection or get_settings().qdrant_collection
    stale = models.Filter(
        must=[models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))],
        must_not=[
            models.FieldCondition(
                key="doc_content_hash", match=models.MatchValue(value=keep_hash)
            )
        ],
    )

    count = client.count(collection_name=collection, count_filter=stale, exact=True).count
    if not count:
        return 0

    client.delete(
        collection_name=collection,
        points_selector=models.FilterSelector(filter=stale),
        wait=True,
    )
    logger.info("removed %d stale points for %s", count, doc_id)
    return count


def delete_documents(
    client: QdrantClient, doc_ids: list[str], collection: str | None = None
) -> int:
    """Remove every point of documents that are gone from disk."""
    if not doc_ids:
        return 0

    collection = collection or get_settings().qdrant_collection
    gone = models.Filter(
        must=[
            models.FieldCondition(key="doc_id", match=models.MatchAny(any=list(doc_ids)))
        ]
    )

    count = client.count(collection_name=collection, count_filter=gone, exact=True).count
    client.delete(
        collection_name=collection,
        points_selector=models.FilterSelector(filter=gone),
        wait=True,
    )
    logger.info("deleted %d points for %d removed documents", count, len(doc_ids))
    return count
