"""The collection schema: named dense + sparse vectors, and the mismatch guard.

In-memory Qdrant, no models — the vector width comes from settings precisely so
this can be checked without loading BGE-M3.
"""
import pytest
from qdrant_client import QdrantClient, models

from common.config import get_settings
from common.vector_store import (
    DENSE_DISTANCE,
    DENSE_VECTOR,
    SPARSE_VECTOR,
    CollectionMismatch,
    ensure_collection,
)

pytestmark = pytest.mark.ingest

COLLECTION = "test_chunks"


@pytest.fixture
def client() -> QdrantClient:
    return QdrantClient(":memory:")


def dense_params(client: QdrantClient) -> models.VectorParams:
    return client.get_collection(COLLECTION).config.params.vectors[DENSE_VECTOR]


class TestCreation:
    def test_dense_vector_matches_the_configured_width(self, client) -> None:
        ensure_collection(client, COLLECTION)

        assert dense_params(client).size == get_settings().embedding_dimensions

    def test_dense_vector_uses_the_configured_distance(self, client) -> None:
        """Dot, which is only equivalent to cosine while embeddings are
        normalised — see the note in `common/vector_store.py`."""
        ensure_collection(client, COLLECTION)

        assert dense_params(client).distance == DENSE_DISTANCE

    def test_sparse_vector_exists(self, client) -> None:
        """Both vectors on one point, so a hybrid query fuses server-side."""
        ensure_collection(client, COLLECTION)

        config = client.get_collection(COLLECTION).config.params
        assert SPARSE_VECTOR in config.sparse_vectors

    def test_doc_id_is_indexed(self, client, monkeypatch) -> None:
        """Every state read and delete filters on it; without an index Qdrant
        scans the collection each time.

        Asserted as a call rather than by reading the schema back: the local
        Qdrant accepts payload indexes and ignores them, so the schema is empty
        there however the code behaves.
        """
        indexed = []
        monkeypatch.setattr(
            client,
            "create_payload_index",
            lambda **kwargs: indexed.append(kwargs["field_name"]),
        )

        ensure_collection(client, COLLECTION)

        assert indexed == ["doc_id"]


class TestIdempotence:
    def test_calling_twice_is_not_an_error(self, client) -> None:
        """Every run calls it; only the first should create anything."""
        ensure_collection(client, COLLECTION)
        ensure_collection(client, COLLECTION)

        assert client.collection_exists(COLLECTION)


class TestMismatchGuard:
    def test_wrong_dense_width_is_refused(self, client) -> None:
        """Fires when the embedding model changes without a rebuild. Writing
        anyway would mix incompatible vectors and only show up as worse
        answers."""
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config={
                DENSE_VECTOR: models.VectorParams(size=384, distance=DENSE_DISTANCE)
            },
        )

        with pytest.raises(CollectionMismatch, match="384"):
            ensure_collection(client, COLLECTION)

    def test_missing_dense_vector_is_refused(self, client) -> None:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config={
                "other": models.VectorParams(
                    size=get_settings().embedding_dimensions, distance=DENSE_DISTANCE
                )
            },
        )

        with pytest.raises(CollectionMismatch, match=DENSE_VECTOR):
            ensure_collection(client, COLLECTION)

    def test_the_error_says_how_to_recover(self, client) -> None:
        """A schema mismatch is not self-healing; the message has to name the
        fix or it just reads as a crash."""
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config={
                DENSE_VECTOR: models.VectorParams(size=384, distance=DENSE_DISTANCE)
            },
        )

        with pytest.raises(CollectionMismatch, match="re-run ingestion"):
            ensure_collection(client, COLLECTION)
