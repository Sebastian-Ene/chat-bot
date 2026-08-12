"""State is read from Qdrant, so these run against a real in-memory Qdrant
rather than a stub — the scroll path is the thing worth testing.
"""
from pathlib import Path

import pytest
from qdrant_client import QdrantClient, models

from app.rag.ingest.discovery import DiscoveredDocument
from app.rag.ingest.state import indexed_documents, plan

pytestmark = pytest.mark.ingest

COLLECTION = "chunks"


def document(doc_id: str, content_hash: str) -> DiscoveredDocument:
    return DiscoveredDocument(
        doc_id=doc_id,
        path=Path("/corpus") / doc_id,
        source_format=doc_id.rsplit(".", 1)[-1],
        size_bytes=1,
        content_hash=content_hash,
    )


@pytest.fixture
def client() -> QdrantClient:
    return QdrantClient(":memory:")


def index(client: QdrantClient, points: list[tuple[str, str]]) -> None:
    """`points` is (doc_id, content_hash) — one chunk each is enough here."""
    client.create_collection(
        COLLECTION, vectors_config=models.VectorParams(size=2, distance=models.Distance.COSINE)
    )
    client.upsert(
        COLLECTION,
        points=[
            models.PointStruct(
                id=index_,
                vector=[0.1, 0.2],
                payload={"doc_id": doc_id, "doc_content_hash": content_hash},
            )
            for index_, (doc_id, content_hash) in enumerate(points)
        ],
    )


class TestIndexedDocuments:
    def test_missing_collection_means_nothing_is_indexed(self, client: QdrantClient) -> None:
        assert indexed_documents(client, COLLECTION) == {}

    def test_collects_hashes_per_document(self, client: QdrantClient) -> None:
        index(client, [("a.pdf", "hash-a"), ("a.pdf", "hash-a"), ("b.pdf", "hash-b")])

        assert indexed_documents(client, COLLECTION) == {
            "a.pdf": {"hash-a"},
            "b.pdf": {"hash-b"},
        }

    def test_reads_every_point_beyond_one_scroll_batch(self, client: QdrantClient) -> None:
        index(client, [(f"doc-{n}.pdf", f"hash-{n}") for n in range(2500)])

        assert len(indexed_documents(client, COLLECTION)) == 2500


class TestPlan:
    def test_unindexed_document_is_new(self) -> None:
        result = plan([document("a.pdf", "hash-a")], {})

        assert [d.doc_id for d in result.new] == ["a.pdf"]
        assert result.has_work

    def test_same_hash_is_unchanged(self) -> None:
        result = plan([document("a.pdf", "hash-a")], {"a.pdf": {"hash-a"}})

        assert [d.doc_id for d in result.unchanged] == ["a.pdf"]
        assert not result.has_work

    def test_different_hash_is_changed(self) -> None:
        result = plan([document("a.pdf", "hash-new")], {"a.pdf": {"hash-old"}})

        assert [d.doc_id for d in result.changed] == ["a.pdf"]

    def test_document_gone_from_disk_is_deleted(self) -> None:
        result = plan([], {"a.pdf": {"hash-a"}})

        assert result.deleted == ["a.pdf"]
        assert result.has_work

    def test_several_hashes_means_a_partial_write_and_is_re_ingested(self) -> None:
        """A document should only ever carry one hash; more means it was written
        half-way, so it cannot be trusted as indexed."""
        result = plan([document("a.pdf", "hash-a")], {"a.pdf": {"hash-a", "hash-old"}})

        assert [d.doc_id for d in result.changed] == ["a.pdf"]

    def test_to_index_covers_new_and_changed_only(self) -> None:
        result = plan(
            [
                document("new.pdf", "h1"),
                document("changed.pdf", "h2"),
                document("same.pdf", "h3"),
            ],
            {"changed.pdf": {"old"}, "same.pdf": {"h3"}},
        )

        assert [d.doc_id for d in result.to_index] == ["new.pdf", "changed.pdf"]

    def test_summary_reports_every_bucket(self) -> None:
        result = plan([document("a.pdf", "h")], {"gone.pdf": {"x"}})

        assert result.summary() == "new=1 changed=0 unchanged=0 deleted=1"
