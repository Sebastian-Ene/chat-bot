"""Converter configuration and the failure path — no models loaded here.

Parsing real documents lives in `test_parse_documents.py`, behind the `docling`
marker.
"""
from pathlib import Path

import pytest

from app.rag.ingest.discovery import DiscoveredDocument
from app.rag.ingest.parse import ParseFailed, _pdf_options, get_converter, parse, parse_all

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

    def test_parse_all_skips_the_failure_and_keeps_going(self) -> None:
        """One malformed file must not block the rest of the corpus."""
        parsed, failed = parse_all([document("a.pdf"), document("b.pdf")])

        assert parsed == []
        assert failed == ["a.pdf", "b.pdf"]

    def test_failures_are_logged_at_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Production alerts on these, so a document that never parses cannot
        disappear quietly."""
        import logging

        from app.logging_config import INGEST_LOGGER

        with caplog.at_level(logging.ERROR, logger=INGEST_LOGGER):
            parse_all([document("broken.pdf")])

        assert "parse failed" in caplog.text
        assert "broken.pdf" in caplog.text
