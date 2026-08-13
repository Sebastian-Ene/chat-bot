"""Parsing a document into a `DoclingDocument`.

One converter is built for the process and reused: it loads layout, table and
OCR models, so constructing it per document would dominate a run.

Conversion failures raise `ParseFailed`; the runner turns that into a skipped
document and an ERROR line naming the file. One malformed file must not block
the rest of the corpus, and because what is indexed is read back from the
collection, a skipped document is simply still missing and gets retried on the
next run, with no bookkeeping to keep straight. In production those ERROR lines
would be alerted on, so a document that never parses cannot fail silently.
"""
import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from time import perf_counter

# torch JIT-compiles through inductor/triton, which needs a C compiler that is
# not present. Must be set before torch is imported anywhere below.
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")

from docling.datamodel.base_models import InputFormat  # noqa: E402
from docling.datamodel.pipeline_options import PdfPipelineOptions  # noqa: E402
from docling.document_converter import DocumentConverter, PdfFormatOption  # noqa: E402
from docling_core.types.doc.document import DoclingDocument  # noqa: E402

from common.logging_config import INGEST_LOGGER  # noqa: E402
from ingestion.discovery import DiscoveredDocument  # noqa: E402

logger = logging.getLogger(INGEST_LOGGER)

# Figures are rendered at twice their layout size: the caption stage and OCR
# both read them, and the source images are small diagrams and charts.
IMAGE_SCALE = 2.0


class ParseFailed(Exception):
    """Docling could not convert the document."""


@dataclass(frozen=True)
class ParsedDocument:
    """A converted document, with the counts worth logging and asserting on."""

    doc_id: str
    source_format: str
    content_hash: str
    document: DoclingDocument
    seconds: float

    @property
    def page_count(self) -> int:
        """Zero for DOCX and HTML — only PDF carries page provenance."""
        return len(self.document.pages)

    @property
    def table_count(self) -> int:
        return len(self.document.tables)

    @property
    def picture_count(self) -> int:
        return len(self.document.pictures)


def _pdf_options() -> PdfPipelineOptions:
    options = PdfPipelineOptions()
    # OCR reads text rendered *inside* images — chart axis labels, legends,
    # numbers in diagrams — which the captioner does not reliably transcribe.
    options.do_ocr = True
    options.do_table_structure = True
    # Without this Docling discards figure images after layout analysis, and the
    # caption stage has nothing to describe.
    options.generate_picture_images = True
    options.images_scale = IMAGE_SCALE
    return options


@lru_cache(maxsize=1)
def get_converter() -> DocumentConverter:
    """Built once per process: it loads several models."""
    logger.info("loading docling converter (layout, table structure, OCR)")
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=_pdf_options())}
    )
    logger.info("docling converter ready")
    return converter


def parse(document: DiscoveredDocument) -> ParsedDocument:
    """Convert one document. Raises `ParseFailed` so the caller can skip it."""
    started = perf_counter()
    try:
        result = get_converter().convert(str(document.path))
    except Exception as error:
        raise ParseFailed(
            f"{document.doc_id}: {type(error).__name__}: {error}"
        ) from error

    parsed = ParsedDocument(
        doc_id=document.doc_id,
        source_format=document.source_format,
        content_hash=document.content_hash,
        document=result.document,
        seconds=round(perf_counter() - started, 2),
    )
    logger.info(
        "parsed %s pages=%d tables=%d pictures=%d seconds=%.2f",
        parsed.doc_id,
        parsed.page_count,
        parsed.table_count,
        parsed.picture_count,
        parsed.seconds,
    )
    return parsed


