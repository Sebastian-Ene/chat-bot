"""What is already indexed, and what an ingestion run therefore has to do.

The collection is the record: each chunk payload carries `doc_id` and
`doc_content_hash`, so what is indexed — and at which version — is read straight
from Qdrant and compared against the files on disk.

This relies on **all of a document's points being written in one upsert**, so a
document is atomically present at a given hash or not present at all. A document
carrying more than one hash is treated as incomplete and re-ingested.
"""
import logging
from dataclasses import dataclass, field

from qdrant_client import QdrantClient

from app.config import get_settings
from app.logging_config import INGEST_LOGGER
from app.rag.ingest.discovery import DiscoveredDocument

logger = logging.getLogger(INGEST_LOGGER)

_SCROLL_BATCH = 1000


@dataclass(frozen=True)
class IngestPlan:
    """What the run will do. `unchanged` documents are skipped entirely."""

    new: list[DiscoveredDocument] = field(default_factory=list)
    changed: list[DiscoveredDocument] = field(default_factory=list)
    unchanged: list[DiscoveredDocument] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)  # doc_ids no longer on disk

    @property
    def to_index(self) -> list[DiscoveredDocument]:
        return [*self.new, *self.changed]

    @property
    def has_work(self) -> bool:
        return bool(self.new or self.changed or self.deleted)

    def summary(self) -> str:
        return (
            f"new={len(self.new)} changed={len(self.changed)} "
            f"unchanged={len(self.unchanged)} deleted={len(self.deleted)}"
        )


def indexed_documents(client: QdrantClient, collection: str | None = None) -> dict[str, set[str]]:
    """Map `doc_id` to the content hashes present for it in the collection.

    Normally one hash per document. More than one means a half-written document,
    which the plan treats as needing re-ingestion.
    """
    collection = collection or get_settings().qdrant_collection
    if not client.collection_exists(collection):
        # Nothing indexed yet — the first run has everything to do.
        return {}

    indexed: dict[str, set[str]] = {}
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=collection,
            limit=_SCROLL_BATCH,
            offset=offset,
            with_payload=["doc_id", "doc_content_hash"],
            with_vectors=False,
        )
        for point in points:
            payload = point.payload or {}
            doc_id = payload.get("doc_id")
            content_hash = payload.get("doc_content_hash")
            if doc_id and content_hash:
                indexed.setdefault(doc_id, set()).add(content_hash)
        if offset is None:
            break

    return indexed


def plan(discovered: list[DiscoveredDocument], indexed: dict[str, set[str]]) -> IngestPlan:
    """Compare what is on disk against what is in the collection."""
    on_disk = {document.doc_id for document in discovered}
    result = IngestPlan(deleted=sorted(set(indexed) - on_disk))

    for document in discovered:
        hashes = indexed.get(document.doc_id)
        if not hashes:
            result.new.append(document)
        elif hashes == {document.content_hash}:
            result.unchanged.append(document)
        else:
            # Different hash, or several — changed content, or a partial write.
            result.changed.append(document)

    return result


def build_plan(client: QdrantClient, discovered: list[DiscoveredDocument]) -> IngestPlan:
    indexed = indexed_documents(client)
    result = plan(discovered, indexed)

    logger.info(
        "ingestion plan %s (indexed already=%d)", result.summary(), len(indexed)
    )
    for document in result.to_index:
        logger.debug("will index %s hash=%s", document.doc_id, document.short_hash)
    for doc_id in result.deleted:
        logger.info("gone from disk, vectors to remove: %s", doc_id)
    if not result.has_work:
        logger.info("nothing to do — corpus unchanged since the last run")
    return result
