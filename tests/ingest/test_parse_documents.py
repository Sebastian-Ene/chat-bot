"""Parsing real corpus documents with real models.

Slow — loads layout, table and OCR models — so it sits behind the `docling`
marker and out of the default run:

    uv run pytest -m docling

These pin the findings the design depends on, so a Docling upgrade that changes
them fails here rather than silently producing an unindexed corpus.
"""
import pytest

from app.rag.ingest.discovery import discover
from app.rag.ingest.parse import parse

pytestmark = [pytest.mark.ingest, pytest.mark.docling]

COVERAGE = "corpus/docs-initial/coverage"
BULK = "corpus/docs-initial/bulk"


def parse_one(directory: str, name: str):
    from pathlib import Path

    documents = {document.doc_id: document for document in discover(Path(directory))}
    assert name in documents, f"{name} missing from {directory}"
    return parse(documents[name])


@pytest.fixture(scope="module")
def technical_pdf():
    """German PDF: unruled tables and an uncaptioned chart."""
    return parse_one(COVERAGE, "aurora-technische-daten-de.pdf")


@pytest.fixture(scope="module")
def catalogue_docx():
    """DOCX carrying a figure."""
    return parse_one(BULK, "accessory-catalogue-en.docx")


@pytest.fixture(scope="module")
def faq_html():
    """HTML carrying a figure."""
    return parse_one(COVERAGE, "aurora-support-faq.html")


class TestPdf:
    def test_has_pages_tables_and_a_picture(self, technical_pdf) -> None:
        assert technical_pdf.page_count == 3
        assert technical_pdf.table_count == 2, "the unruled spec tables"
        assert technical_pdf.picture_count == 1

    def test_picture_carries_image_bytes(self, technical_pdf) -> None:
        """The caption stage needs pixels; PDF provides them."""
        picture = technical_pdf.document.pictures[0]

        assert picture.get_image(technical_pdf.document) is not None


class TestDocx:
    def test_pages_are_not_available(self, catalogue_docx) -> None:
        """`page_no` can only ever be populated for PDF."""
        assert catalogue_docx.page_count == 0

    def test_picture_carries_image_bytes(self, catalogue_docx) -> None:
        picture = catalogue_docx.document.pictures[0]

        assert picture.get_image(catalogue_docx.document) is not None


class TestHtml:
    def test_picture_is_found(self, faq_html) -> None:
        assert faq_html.picture_count == 1

    def test_picture_has_no_image_bytes(self, faq_html) -> None:
        """The gap the design has to work around: HTML figures arrive without
        pixels, so their images must be loaded from the `<img src>` ourselves."""
        picture = faq_html.document.pictures[0]

        assert picture.get_image(faq_html.document) is None
