"""Converter configuration and the failure path — no models loaded here.

Parsing real documents lives in `test_parse_documents.py`, behind the `docling`
marker.
"""
from pathlib import Path

import pytest

from app.rag.ingest.discovery import DiscoveredDocument
from app.rag.ingest.parse import ParseFailed, _pdf_options, get_converter, parse

pytestmark = pytest.mark.ingest


def document(doc_id: str = "a.pdf") -> DiscoveredDocument:
    return DiscoveredDocument(
        doc_id=doc_id,
        path=Path("/corpus") / doc_id,
        source_format="pdf",
        size_bytes=1,
        content_hash="hash",
    )


class TestPdfOptions:
    def test_ocr_is_on(self) -> None:
        """OCR reads text inside figures, which the captioner does not."""
        assert _pdf_options().do_ocr is True

    def test_table_structure_is_on(self) -> None:
        assert _pdf_options().do_table_structure is True

    def test_picture_images_are_kept(self) -> None:
        """Without this Docling discards figure images and the caption stage
        has nothing to work with."""
        assert _pdf_options().generate_picture_images is True


def test_converter_is_built_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """It loads several models, so rebuilding per document would dominate."""
    get_converter.cache_clear()
    calls = []

    class FakeConverter:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr("app.rag.ingest.parse.DocumentConverter", FakeConverter)
    get_converter()
    get_converter()

    assert len(calls) == 1
    get_converter.cache_clear()


class TestFailureHandling:
    @pytest.fixture(autouse=True)
    def failing_converter(self, monkeypatch: pytest.MonkeyPatch):
        class Boom:
            def convert(self, _path):
                raise RuntimeError("corrupt file")

        get_converter.cache_clear()
        monkeypatch.setattr("app.rag.ingest.parse.get_converter", lambda: Boom())
        yield
        get_converter.cache_clear()

    def test_parse_raises_parse_failed(self) -> None:
        with pytest.raises(ParseFailed, match="corrupt file"):
            parse(document())

    def test_error_names_the_document(self) -> None:
        with pytest.raises(ParseFailed, match="broken.pdf"):
            parse(document("broken.pdf"))

    def test_the_underlying_error_is_preserved(self) -> None:
        """The runner logs this text; a bare "parse failed" would not say what
        to fix."""
        with pytest.raises(ParseFailed, match="RuntimeError"):
            parse(document("broken.pdf"))
