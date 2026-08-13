"""Writing chunks into Qdrant: ids, payload, and replacing a document.

In-memory Qdrant with hand-made vectors — no models. The vectors are arbitrary;
what is under test is what lands in the collection and what is removed.
"""
import pytest
from qdrant_client import QdrantClient, models

from app.config import get_settings
from app.embedding import Embedding
from app.rag.ingest.chunk import Chunk
from app.rag.ingest.index import (
    delete_documents,
    delete_stale,
    index_document,
    point_id,
    to_points,
)
from app.vector_store import DENSE_VECTOR, SPARSE_VECTOR, ensure_collection

pytestmark = pytest.mark.ingest

COLLECTION = "test_chunks"


@pytest.fixture
def client() -> QdrantClient:
    client = QdrantClient(":memory:")
    ensure_collection(client, COLLECTION)
    return client


def chunk(
    doc_id: str = "a.pdf",
    index: int = 0,
    content_hash: str = "hash-1",
    text: str = "body",
    pages: list[int] | None = None,
    headings: list[str] | None = None,
    source_format: str = "pdf",
) -> Chunk:
    return Chunk(
        doc_id=doc_id,
        doc_content_hash=content_hash,
        chunk_index=index,
        text=text,
        embed_text=f"context > {text}",
        source_format=source_format,
        headings=headings if headings is not None else ["Heading"],
        page_numbers=pages if pages is not None else [1],
    )


def embedding(seed: float = 0.1) -> Embedding:
    dimensions = get_settings().embedding_dimensions
    return Embedding(dense=[seed] * dimensions, sparse={7: 0.5, 42: 0.25})


def write(client: QdrantClient, chunks: list[Chunk]) -> int:
    return index_document(client, chunks, [embedding() for _ in chunks], COLLECTION)


def stored(client: QdrantClient) -> list[models.Record]:
    points, _ = client.scroll(collection_name=COLLECTION, limit=100, with_payload=True)
    return points


class TestPointIds:
    def test_are_stable_across_runs(self) -> None:
        """Re-ingesting must overwrite in place, not accumulate duplicates."""
        assert point_id("a.pdf", 3) == point_id("a.pdf", 3)

    def test_differ_per_chunk(self) -> None:
        assert point_id("a.pdf", 0) != point_id("a.pdf", 1)

    def test_differ_per_document(self) -> None:
        assert point_id("a.pdf", 0) != point_id("b.pdf", 0)


class TestPayload:
    def test_carries_the_chunk_text(self, client) -> None:
        """Retrieval answers in one round trip; the api never reads the corpus."""
        write(client, [chunk(text="Reset the hub")])

        assert stored(client)[0].payload["text"] == "Reset the hub"

    def test_does_not_store_the_contextualised_text(self, client) -> None:
        """It exists only to be vectorised — storing it puts heading
        breadcrumbs one careless line away from the prompt."""
        write(client, [chunk(text="Reset the hub")])

        assert "embed_text" not in stored(client)[0].payload

    def test_carries_the_document_hash(self, client) -> None:
        """`state.py` reads this back to decide what a run has to do."""
        write(client, [chunk(content_hash="abc")])

        assert stored(client)[0].payload["doc_content_hash"] == "abc"

    def test_carries_provenance(self, client) -> None:
        write(client, [chunk(pages=[2, 3], headings=["Troubleshooting"])])

        payload = stored(client)[0].payload
        assert payload["page_numbers"] == [2, 3]
        assert payload["headings"] == ["Troubleshooting"]

    def test_tolerates_a_chunk_with_no_pages(self, client) -> None:
        """HTML and DOCX carry no page provenance."""
        write(client, [chunk(doc_id="a.html", source_format="html", pages=[])])

        assert stored(client)[0].payload["page_numbers"] == []


class TestVectors:
    def test_both_named_vectors_are_written(self, client) -> None:
        write(client, [chunk()])

        points, _ = client.scroll(
            collection_name=COLLECTION, limit=1, with_vectors=True
        )
        assert DENSE_VECTOR in points[0].vector
        assert SPARSE_VECTOR in points[0].vector

    def test_sparse_becomes_parallel_arrays(self) -> None:
        points = to_points([chunk()], [embedding()])

        sparse = points[0].vector[SPARSE_VECTOR]
        assert sparse.indices == [7, 42]
        assert sparse.values == [0.5, 0.25]


class TestIndexDocument:
    def test_writes_one_point_per_chunk(self, client) -> None:
        written = write(client, [chunk(index=0), chunk(index=1)])

        assert written == 2
        assert len(stored(client)) == 2

    def test_a_single_upsert_per_document(self, client, monkeypatch) -> None:
        """The invariant `state.py` depends on: a document is indexed at a hash
        or it is not — never half-written."""
        calls = []
        monkeypatch.setattr(
            client, "upsert", lambda **kwargs: calls.append(kwargs["points"])
        )

        index_document(
            client,
            [chunk(index=0), chunk(index=1), chunk(index=2)],
            [embedding()] * 3,
            COLLECTION,
        )

        assert len(calls) == 1
        assert len(calls[0]) == 3

    def test_no_chunks_writes_nothing(self, client, monkeypatch) -> None:
        calls = []
        monkeypatch.setattr(client, "upsert", lambda **kwargs: calls.append(kwargs))

        assert index_document(client, [], [], COLLECTION) == 0
        assert calls == []


class TestReplacingADocument:
    def test_reindexing_the_same_version_does_not_duplicate(self, client) -> None:
        write(client, [chunk(index=0), chunk(index=1)])
        write(client, [chunk(index=0), chunk(index=1)])

        assert len(stored(client)) == 2

    def test_a_shorter_new_version_leaves_no_orphans(self, client) -> None:
        """Deterministic ids overwrite chunk-for-chunk, so a version with fewer
        chunks would strand the tail as unreachable context."""
        write(client, [chunk(index=i, content_hash="old") for i in range(3)])

        write(client, [chunk(index=0, content_hash="new")])
        delete_stale(client, "a.pdf", "new", COLLECTION)

        remaining = stored(client)
        assert len(remaining) == 1
        assert remaining[0].payload["doc_content_hash"] == "new"

    def test_other_documents_are_untouched(self, client) -> None:
        write(client, [chunk(doc_id="b.pdf", content_hash="other")])
        write(client, [chunk(content_hash="new")])

        delete_stale(client, "a.pdf", "new", COLLECTION)

        assert {p.payload["doc_id"] for p in stored(client)} == {"a.pdf", "b.pdf"}

    def test_nothing_stale_is_a_no_op(self, client) -> None:
        write(client, [chunk(content_hash="new")])

        assert delete_stale(client, "a.pdf", "new", COLLECTION) == 0


class TestDeletingDocuments:
    def test_removes_every_point_of_a_gone_document(self, client) -> None:
        write(client, [chunk(index=0), chunk(index=1)])
        write(client, [chunk(doc_id="b.pdf")])

        deleted = delete_documents(client, ["a.pdf"], COLLECTION)

        assert deleted == 2
        assert {p.payload["doc_id"] for p in stored(client)} == {"b.pdf"}

    def test_an_empty_list_is_a_no_op(self, client, monkeypatch) -> None:
        calls = []
        monkeypatch.setattr(client, "delete", lambda **kwargs: calls.append(kwargs))

        assert delete_documents(client, [], COLLECTION) == 0
        assert calls == []
