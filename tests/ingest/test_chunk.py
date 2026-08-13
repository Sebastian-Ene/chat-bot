"""Chunk construction and metadata — no tokenizer, no models.

Real chunking of real documents lives in `test_chunk_documents.py`, behind the
`docling` marker.
"""
from dataclasses import dataclass

import pytest

from ingestion.chunk import Chunk, chunk, get_chunker

pytestmark = pytest.mark.ingest


@dataclass
class FakeProv:
    page_no: int | None


@dataclass
class FakeItem:
    prov: list[FakeProv]


@dataclass
class FakeMeta:
    headings: list[str] | None
    doc_items: list[FakeItem]


@dataclass
class FakeDocChunk:
    text: str
    meta: FakeMeta


@dataclass
class FakeParsed:
    """Stands in for a ParsedDocument — only the fields chunking reads."""

    doc_id: str = "a.pdf"
    source_format: str = "pdf"
    content_hash: str = "hash"
    document: object = None


def doc_chunk(text="body", headings=None, pages=()) -> FakeDocChunk:
    return FakeDocChunk(
        text=text,
        meta=FakeMeta(
            headings=headings,
            doc_items=[FakeItem(prov=[FakeProv(page_no=page) for page in pages])],
        ),
    )


@pytest.fixture
def chunker(monkeypatch: pytest.MonkeyPatch):
    """A chunker whose output the test controls."""

    class FakeChunker:
        chunks: list[FakeDocChunk] = []

        def chunk(self, _document):
            return iter(self.chunks)

        def contextualize(self, doc_chunk):
            return " > ".join([*(doc_chunk.meta.headings or []), doc_chunk.text])

    fake = FakeChunker()
    monkeypatch.setattr("ingestion.chunk.get_chunker", lambda: fake)
    return fake


class TestChunkIndex:
    def test_is_sequential_from_zero(self, chunker) -> None:
        chunker.chunks = [doc_chunk("one"), doc_chunk("two"), doc_chunk("three")]

        assert [c.chunk_index for c in chunk(FakeParsed())] == [0, 1, 2]

    def test_an_empty_document_yields_no_chunks(self, chunker) -> None:
        """Not an error: a document can legitimately hold nothing chunkable."""
        chunker.chunks = []

        assert chunk(FakeParsed()) == []


class TestTexts:
    def test_embed_text_carries_the_heading_path(self, chunker) -> None:
        """Why both texts exist: "Reset the hub" is only findable as belonging
        to Troubleshooting once the headings travel with it."""
        chunker.chunks = [doc_chunk("Reset the hub", headings=["Troubleshooting"])]

        result = chunk(FakeParsed())[0]

        assert result.text == "Reset the hub"
        assert result.embed_text == "Troubleshooting > Reset the hub"

    def test_raw_text_is_what_gets_cited(self, chunker) -> None:
        """The prompt must not carry synthetic breadcrumbs into the answer."""
        chunker.chunks = [doc_chunk("Reset the hub", headings=["Troubleshooting"])]

        assert "Troubleshooting" not in chunk(FakeParsed())[0].text


class TestPageNumbers:
    def test_are_deduplicated_and_sorted(self, chunker) -> None:
        chunker.chunks = [doc_chunk(pages=(3, 1, 3))]

        assert chunk(FakeParsed())[0].page_numbers == [1, 3]

    def test_are_empty_when_the_format_has_no_pages(self, chunker) -> None:
        """DOCX and HTML carry no page provenance; citations must tolerate it."""
        chunker.chunks = [doc_chunk(pages=(None,))]

        result = chunk(FakeParsed(doc_id="a.docx", source_format="docx"))[0]

        assert result.page_numbers == []


class TestDocumentIdentity:
    def test_every_chunk_carries_the_document_hash(self, chunker) -> None:
        """Indexing and the plan both key on it — a chunk without it cannot be
        matched to the version of the document it came from."""
        chunker.chunks = [doc_chunk("one"), doc_chunk("two")]

        chunks = chunk(FakeParsed(doc_id="b.pdf", content_hash="abc123"))

        assert {c.doc_id for c in chunks} == {"b.pdf"}
        assert {c.doc_content_hash for c in chunks} == {"abc123"}


def test_chunker_is_built_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """It loads a tokenizer, so rebuilding per document would show up."""
    get_chunker.cache_clear()
    calls = []

    class FakeTokenizer:
        @classmethod
        def from_pretrained(cls, **kwargs):
            calls.append(kwargs)
            return cls()

    monkeypatch.setattr("ingestion.chunk.HuggingFaceTokenizer", FakeTokenizer)
    monkeypatch.setattr("ingestion.chunk.HybridChunker", lambda **_kwargs: object())

    get_chunker()
    get_chunker()

    assert len(calls) == 1
    get_chunker.cache_clear()


def test_chunker_is_sized_in_the_embedding_models_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A chunk measured in another tokenizer's tokens overflows silently at
    embed time — the tail is truncated and never retrievable."""
    get_chunker.cache_clear()
    calls = []

    class FakeTokenizer:
        @classmethod
        def from_pretrained(cls, **kwargs):
            calls.append(kwargs)
            return cls()

    monkeypatch.setattr("ingestion.chunk.HuggingFaceTokenizer", FakeTokenizer)
    monkeypatch.setattr("ingestion.chunk.HybridChunker", lambda **_kwargs: object())

    get_chunker()

    from ingestion.config import get_settings

    assert calls[0]["model_name"] == get_settings().embedding_model
    assert calls[0]["max_tokens"] == get_settings().chunk_max_tokens
    get_chunker.cache_clear()
