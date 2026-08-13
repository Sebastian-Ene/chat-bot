"""Embedding plumbing — no model loaded.

The real model is exercised in `tests/ingest/test_embedding_model.py`, behind
the `embedding` marker.
"""
import numpy as np
import pytest

from common.embedding import Embedding, embed_documents, embed_query, get_embedder


@pytest.fixture
def model(monkeypatch: pytest.MonkeyPatch):
    """Records every encode call so tests can assert on the arguments."""

    class FakeModel:
        calls: list[dict] = []

        def encode(self, sentences, **kwargs):
            self.calls.append({"sentences": sentences, **kwargs})
            return {
                "dense_vecs": np.array([[0.1, 0.2]] * len(sentences)),
                "lexical_weights": [{"101": 0.5, "202": 0.25}] * len(sentences),
            }

    fake = FakeModel()
    fake.calls = []
    monkeypatch.setattr("common.embedding.get_embedder", lambda: fake)
    return fake


class TestSparseConversion:
    def test_token_ids_become_integers(self, model) -> None:
        """FlagEmbedding keys them as strings; Qdrant needs integer indices."""
        result = embed_documents(["hello"])[0]

        assert result.sparse == {101: 0.5, 202: 0.25}

    def test_converts_to_parallel_arrays(self) -> None:
        embedding = Embedding(dense=[], sparse={202: 0.25, 101: 0.5})

        indices, values = embedding.sparse_indices_and_values()

        assert indices == [101, 202]
        assert values == [0.5, 0.25]

    def test_empty_sparse_gives_empty_arrays(self) -> None:
        assert Embedding(dense=[], sparse={}).sparse_indices_and_values() == ([], [])


class TestEmbedDocuments:
    def test_returns_one_embedding_per_text(self, model) -> None:
        assert len(embed_documents(["a", "b", "c"])) == 3

    def test_empty_input_skips_the_model(self, model) -> None:
        """Loading and calling the model for nothing costs seconds."""
        assert embed_documents([]) == []
        assert model.calls == []

    def test_requests_both_vector_kinds(self, model) -> None:
        """Hybrid retrieval needs both, and they come from one forward pass."""
        embed_documents(["a"])

        assert model.calls[0]["return_dense"] is True
        assert model.calls[0]["return_sparse"] is True

    def test_skips_colbert_vectors(self, model) -> None:
        """Unused, and they are the expensive part of the output."""
        embed_documents(["a"])

        assert model.calls[0]["return_colbert_vecs"] is False

    def test_uses_the_configured_batch_size(self, model) -> None:
        from common.config import get_settings

        embed_documents(["a"])

        assert model.calls[0]["batch_size"] == get_settings().embed_batch_size


class TestEmbedQuery:
    def test_returns_a_single_embedding(self, model) -> None:
        result = embed_query("wie setze ich den hub zurück")

        assert isinstance(result, Embedding)
        assert result.sparse == {101: 0.5, 202: 0.25}

    def test_asks_for_the_same_vector_kinds_as_documents(self, model) -> None:
        """A query embedded differently from the chunks cannot match them, and
        the failure looks like bad retrieval rather than a bug."""
        embed_query("q")
        embed_documents(["d"])

        query_call, document_call = model.calls
        assert query_call["return_dense"] == document_call["return_dense"]
        assert query_call["return_sparse"] == document_call["return_sparse"]


class TestModelConfiguration:
    def test_max_length_clears_the_chunk_budget(self) -> None:
        """The chunker's heading path pushes some chunks past the chunk budget;
        an embed limit at the budget would truncate them silently."""
        # Built directly rather than taken from the injected settings: this
        # invariant spans the shared embed budget and the ingest-only chunk
        # budget, and only `IngestSettings` carries both.
        from ingestion.config import IngestSettings

        settings = IngestSettings()

        assert settings.embed_max_tokens > settings.chunk_max_tokens

    def test_model_is_loaded_once(self, monkeypatch: pytest.MonkeyPatch) -> None:
        get_embedder.cache_clear()
        calls = []

        monkeypatch.setattr(
            "common.embedding.BGEM3FlagModel",
            lambda *args, **kwargs: calls.append(kwargs) or object(),
        )

        get_embedder()
        get_embedder()

        assert len(calls) == 1
        get_embedder.cache_clear()

    def test_is_configured_for_cpu_and_normalised_vectors(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """fp16 is a GPU optimisation; normalised vectors make cosine a dot
        product. Both are silent quality/perf regressions if they flip."""
        get_embedder.cache_clear()
        calls = []

        monkeypatch.setattr(
            "common.embedding.BGEM3FlagModel",
            lambda *args, **kwargs: calls.append(kwargs) or object(),
        )

        get_embedder()

        assert calls[0]["use_fp16"] is False
        assert calls[0]["normalize_embeddings"] is True
        get_embedder.cache_clear()
