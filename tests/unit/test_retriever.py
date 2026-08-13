"""Hybrid retrieval: branches, fusion, and what a failure costs.

Runs against in-memory Qdrant with hand-made vectors and a stubbed embedder —
retrieval's own logic is which branches get searched and what comes back, not
whether BGE-M3 works (that is `tests/ingest/test_embedding_model.py`).
"""
import pytest
from qdrant_client import QdrantClient, models

from api.rag.retriever import RetrievalQueries, RetrievedChunk, retrieve
from common import vector_store
from api.core.config import get_settings
from common.embedding import Embedding
from common.vector_store import DENSE_VECTOR, SPARSE_VECTOR, ensure_collection


def test_branches_lists_only_populated_queries() -> None:
    queries = RetrievalQueries(original="support hours", rewritten="opening hours")

    assert queries.branches() == ["original", "rewritten"]


def test_branches_covers_keywords_and_sub_queries() -> None:
    queries = RetrievalQueries(
        original="a",
        rewritten="b",
        keywords=("refund", "window"),
        sub_queries=("c", "d"),
    )

    assert queries.branches() == [
        "original",
        "rewritten",
        "keywords",
        "sub_query[0]",
        "sub_query[1]",
    ]


def test_original_is_the_only_required_query() -> None:
    """A rewrite that fails or is disabled must not remove the raw query."""
    assert RetrievalQueries(original="support hours").branches() == ["original"]


class TestTexts:
    def test_keywords_form_one_branch(self) -> None:
        """They describe a single query; one branch per keyword would let a
        common word outvote the question."""
        queries = RetrievalQueries(original="a", keywords=("refund", "window"))

        assert queries.texts() == ["a", "refund window"]

    def test_texts_line_up_with_branches(self) -> None:
        queries = RetrievalQueries(
            original="a", rewritten="b", keywords=("c",), sub_queries=("d", "e")
        )

        assert len(queries.texts()) == len(queries.branches())


def vector(seed: float) -> list[float]:
    return [seed] * get_settings().embedding_dimensions


@pytest.fixture
def seeded(monkeypatch: pytest.MonkeyPatch) -> QdrantClient:
    """A collection holding two chunks, one clearly closer to the query."""
    client = QdrantClient(":memory:")
    collection = get_settings().qdrant_collection
    ensure_collection(client, collection)
    client.upsert(
        collection_name=collection,
        wait=True,
        points=[
            models.PointStruct(
                id="11111111-1111-5111-8111-111111111111",
                vector={
                    DENSE_VECTOR: vector(1.0),
                    SPARSE_VECTOR: models.SparseVector(indices=[7], values=[1.0]),
                },
                payload={
                    "text": "Fehlercode F250 bedeutet Verbindungsverlust.",
                    "doc_id": "bulk/fehlercode-referenz-de.pdf",
                    "chunk_index": 4,
                    "headings": ["1xx - Netzwerk"],
                    "page_numbers": [12],
                    "source_format": "pdf",
                    "parent_id": "bulk/fehlercode-referenz-de.pdf#1xx - Netzwerk",
                },
            ),
            models.PointStruct(
                id="22222222-2222-5222-8222-222222222222",
                vector={
                    DENSE_VECTOR: vector(-1.0),
                    SPARSE_VECTOR: models.SparseVector(indices=[99], values=[1.0]),
                },
                payload={
                    "text": "Warranty claims within 30 days.",
                    "doc_id": "coverage/warranty-en.html",
                    "chunk_index": 0,
                    "headings": [],
                    "page_numbers": [],
                    "source_format": "html",
                    "parent_id": "coverage/warranty-en.html#",
                },
            ),
        ],
    )
    monkeypatch.setattr(vector_store, "get_client", lambda: client)
    monkeypatch.setattr(
        "api.rag.retriever.embed_documents",
        lambda texts: [
            Embedding(dense=vector(1.0), sparse={7: 1.0}) for _ in texts
        ],
    )
    return client


@pytest.mark.anyio
class TestRetrieve:
    async def test_returns_chunks_with_provenance_not_strings(self, seeded) -> None:
        """The api needs doc_id and pages to attribute an answer."""
        chunks = await retrieve(RetrievalQueries(original="Was bedeutet F250?"))

        assert chunks
        assert all(isinstance(chunk, RetrievedChunk) for chunk in chunks)
        assert chunks[0].doc_id == "bulk/fehlercode-referenz-de.pdf"
        assert chunks[0].page_numbers == [12]

    async def test_ranks_the_matching_chunk_first(self, seeded) -> None:
        chunks = await retrieve(RetrievalQueries(original="Was bedeutet F250?"))

        assert chunks[0].text.startswith("Fehlercode F250")

    async def test_carries_parent_id_for_neighbour_clamping(self, seeded) -> None:
        chunks = await retrieve(RetrievalQueries(original="F250"))

        assert chunks[0].parent_id.startswith("bulk/fehlercode-referenz-de.pdf#")

    async def test_respects_top_k(self, seeded, monkeypatch) -> None:
        monkeypatch.setattr(get_settings(), "retrieval_top_k", 1)

        assert len(await retrieve(RetrievalQueries(original="F250"))) == 1

    async def test_every_branch_is_searched(self, seeded, monkeypatch) -> None:
        """Both vector kinds per branch — dense for meaning, sparse so an error
        code survives as a term."""
        captured = {}
        original_query = seeded.query_points

        def spy(**kwargs):
            captured.update(kwargs)
            return original_query(**kwargs)

        monkeypatch.setattr(seeded, "query_points", spy)

        await retrieve(
            RetrievalQueries(original="a", rewritten="b", keywords=("c",))
        )

        # 3 branches x (dense + sparse)
        assert len(captured["prefetch"]) == 6

    async def test_fuses_with_rrf(self, seeded, monkeypatch) -> None:
        captured = {}
        original_query = seeded.query_points

        def spy(**kwargs):
            captured.update(kwargs)
            return original_query(**kwargs)

        monkeypatch.setattr(seeded, "query_points", spy)

        await retrieve(RetrievalQueries(original="a"))

        assert captured["query"].fusion == models.Fusion.RRF


@pytest.mark.anyio
class TestDegradation:
    async def test_a_missing_collection_returns_nothing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Never ingested is not a crash — the generator says it cannot answer."""
        monkeypatch.setattr(vector_store, "get_client", lambda: QdrantClient(":memory:"))
        monkeypatch.setattr(
            "api.rag.retriever.embed_documents",
            lambda texts: [Embedding(dense=vector(1.0), sparse={}) for _ in texts],
        )

        assert await retrieve(RetrievalQueries(original="anything")) == []

    async def test_a_failure_is_logged_not_raised(
        self, monkeypatch: pytest.MonkeyPatch, caplog
    ) -> None:
        """A broken vector store must degrade the answer, not break the chat."""
        import logging

        class Broken:
            def query_points(self, **_kwargs):
                raise RuntimeError("connection refused")

        monkeypatch.setattr(vector_store, "get_client", lambda: Broken())
        monkeypatch.setattr(
            "api.rag.retriever.embed_documents",
            lambda texts: [Embedding(dense=vector(1.0), sparse={}) for _ in texts],
        )

        with caplog.at_level(logging.ERROR):
            assert await retrieve(RetrievalQueries(original="anything")) == []

        assert "retrieval failed" in caplog.text


class TestCitation:
    def test_includes_pages_when_present(self) -> None:
        chunk = RetrievedChunk(
            text="t", doc_id="a.pdf", chunk_index=0, score=1.0, page_numbers=[3, 4]
        )

        assert chunk.citation() == "a.pdf p.3,4"

    def test_omits_pages_for_formats_without_them(self) -> None:
        """HTML and DOCX have no pages; a citation must not invent one."""
        chunk = RetrievedChunk(text="t", doc_id="a.html", chunk_index=0, score=1.0)

        assert chunk.citation() == "a.html"
