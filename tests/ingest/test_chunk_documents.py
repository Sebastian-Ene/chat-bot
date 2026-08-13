"""Chunking real corpus documents with the real BGE-M3 tokenizer.

Slow — parses the documents and loads a tokenizer — so it sits behind the
`docling` marker:

    uv run pytest -m docling
"""
from pathlib import Path

import pytest

from ingestion.chunk import chunk, get_chunker
from ingestion.discovery import discover
from ingestion.parse import parse

pytestmark = [pytest.mark.ingest, pytest.mark.docling]

COVERAGE = "corpus/docs-initial/coverage"
BULK = "corpus/docs-initial/bulk"

# BGE-M3's own ceiling. Chunks are sized to 512 for precision, not because the
# model demands it, so contextualisation may push `embed_text` slightly past the
# budget without anything being truncated.
MODEL_MAX_TOKENS = 8192


def chunks_for(name: str, directory: str = COVERAGE):
    documents = {d.doc_id: d for d in discover(Path(directory))}
    assert name in documents, f"{name} missing from {directory}"
    return chunk(parse(documents[name]))


@pytest.fixture(scope="module")
def pdf_chunks():
    """German technical PDF: unruled tables, headings, real pages."""
    return chunks_for("aurora-technische-daten-de.pdf")


@pytest.fixture(scope="module")
def html_chunks():
    return chunks_for("aurora-support-faq.html")


@pytest.fixture(scope="module")
def dense_table_chunks():
    """The error-code reference: 25 pages of tables, chunks sitting on the
    budget, and a heading on every one — where contextualisation overflows."""
    return chunks_for("fehlercode-referenz-de.pdf", BULK)


class TestPdf:
    def test_produces_chunks(self, pdf_chunks) -> None:
        assert len(pdf_chunks) > 0

    def test_raw_chunks_respect_the_token_budget(self, pdf_chunks) -> None:
        """Measured with the embedder's own tokenizer — the whole reason the
        chunker is configured with it."""
        tokenizer = get_chunker().tokenizer

        over = [
            c.chunk_index
            for c in pdf_chunks
            if tokenizer.count_tokens(c.text) > tokenizer.get_max_tokens()
        ]

        assert over == []

    def test_chunks_carry_page_numbers(self, pdf_chunks) -> None:
        assert any(c.page_numbers for c in pdf_chunks)

    def test_headings_reach_the_embedded_text(self, pdf_chunks) -> None:
        with_headings = [c for c in pdf_chunks if c.headings]

        assert with_headings, "no chunk carried a heading path"
        assert with_headings[0].embed_text != with_headings[0].text


class TestContextualisationOverflow:
    """Docling sizes a chunk on its raw serialisation, then `contextualize()`
    prepends the heading path — so `embed_text` can exceed the budget by the
    length of that path. Harmless (BGE-M3 takes 8192), but real: 27 of the
    corpus's 207 chunks do it, and code downstream must not assume 512.
    """

    def test_raw_text_still_respects_the_budget(self, dense_table_chunks) -> None:
        tokenizer = get_chunker().tokenizer

        assert all(
            tokenizer.count_tokens(c.text) <= tokenizer.get_max_tokens()
            for c in dense_table_chunks
        )

    def test_contextualisation_can_push_past_the_budget(
        self, dense_table_chunks
    ) -> None:
        tokenizer = get_chunker().tokenizer

        over = [
            c
            for c in dense_table_chunks
            if tokenizer.count_tokens(c.embed_text) > tokenizer.get_max_tokens()
        ]

        assert over, "expected the heading path to overflow at least one chunk"

    def test_nothing_approaches_the_models_real_limit(
        self, dense_table_chunks
    ) -> None:
        """What actually matters: no chunk is truncated at embed time."""
        tokenizer = get_chunker().tokenizer

        assert all(
            tokenizer.count_tokens(c.embed_text) < MODEL_MAX_TOKENS
            for c in dense_table_chunks
        )


class TestHtml:
    def test_produces_chunks(self, html_chunks) -> None:
        assert len(html_chunks) > 0

    def test_chunks_have_no_page_numbers(self, html_chunks) -> None:
        """HTML has no pages; citations must not assume one exists."""
        assert all(c.page_numbers == [] for c in html_chunks)
