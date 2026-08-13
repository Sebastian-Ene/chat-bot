"""BGE-M3 loaded for real.

Several GB of weights, so it sits behind the `embedding` marker:

    uv run pytest -m embedding

These pin the properties the rest of the design assumes — vector width, unit
norm, and that the model actually separates this corpus's languages and topics.
"""
import math

import pytest

from app.config import get_settings
from app.embedding import DENSE_DIMENSIONS, embed_documents, embed_query
from app.rag.ingest.chunk import get_chunker

pytestmark = [pytest.mark.ingest, pytest.mark.embedding]

GERMAN_CHUNK = (
    "Fehlercode F250: Der Hub hat die Verbindung zum Heimnetzwerk verloren. "
    "Starten Sie den Hub neu und prüfen Sie die WLAN-Einstellungen."
)
ENGLISH_CHUNK = (
    "Warranty claims must be submitted within 30 days of delivery, "
    "accompanied by the original proof of purchase."
)


@pytest.fixture(scope="module")
def chunk_embeddings():
    return embed_documents([GERMAN_CHUNK, ENGLISH_CHUNK])


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


class TestDense:
    def test_has_the_width_the_collection_is_sized_for(self, chunk_embeddings) -> None:
        assert all(len(e.dense) == DENSE_DIMENSIONS for e in chunk_embeddings)

    def test_vectors_are_unit_norm(self, chunk_embeddings) -> None:
        """Normalisation is what lets Qdrant's cosine distance be a dot product."""
        for embedding in chunk_embeddings:
            assert math.isclose(cosine(embedding.dense, embedding.dense), 1.0, abs_tol=1e-3)


class TestSparse:
    def test_weights_are_produced(self, chunk_embeddings) -> None:
        assert all(e.sparse for e in chunk_embeddings)

    def test_indices_are_token_ids(self, chunk_embeddings) -> None:
        assert all(
            isinstance(index, int) and index >= 0
            for index in chunk_embeddings[0].sparse
        )

    def test_an_exact_code_is_weighted(self, chunk_embeddings) -> None:
        """The reason sparse is here at all: `F250` must survive as a term, not
        be smeared into a topic vector."""
        code_only = embed_query("F250")

        overlap = set(code_only.sparse) & set(chunk_embeddings[0].sparse)

        assert overlap, "the error code shares no sparse terms with its chunk"


class TestRetrievalBehaviour:
    def test_a_query_is_closest_to_its_own_chunk(self, chunk_embeddings) -> None:
        """The assertion that actually proves the model works for this corpus."""
        query = embed_query("Was bedeutet Fehlercode F250?")
        german, english = chunk_embeddings

        assert cosine(query.dense, german.dense) > cosine(query.dense, english.dense)

    def test_matches_across_languages(self, chunk_embeddings) -> None:
        """Cross-lingual retrieval is why translation was dropped from the
        rewrite step — an English query has to reach a German document."""
        query = embed_query("What does error code F250 mean?")
        german, english = chunk_embeddings

        assert cosine(query.dense, german.dense) > cosine(query.dense, english.dense)


class TestDeterminism:
    def test_the_same_text_embeds_identically(self) -> None:
        """Re-ingesting an unchanged document must not churn the vectors."""
        first, second = embed_documents([GERMAN_CHUNK, GERMAN_CHUNK])

        assert first.dense == second.dense
        assert first.sparse == second.sparse


class TestLongInput:
    def test_text_past_the_chunk_budget_is_not_truncated(self) -> None:
        """FlagEmbedding truncates at 512 by default, which would silently cut
        the chunks whose heading path pushes them over.

        The text is sized between the chunk budget and the embed limit — past
        `embed_max_tokens` both variants would truncate to the same prefix and
        the test would pass for the wrong reason.
        """
        settings = get_settings()
        repetitions = 90  # ~630 tokens: over 512, comfortably under 1024
        long_text = " ".join(["Fehlercode F250 Netzwerk Verbindung"] * repetitions)
        distinct_tail = long_text + " Der Garantieanspruch erlischt nach 30 Tagen."

        tokens = len(get_chunker().tokenizer.get_tokenizer().encode(distinct_tail))
        assert settings.chunk_max_tokens < tokens < settings.embed_max_tokens, (
            f"test text is {tokens} tokens, outside the window it means to probe"
        )

        assert embed_documents([long_text])[0].dense != embed_documents([distinct_tail])[0].dense
