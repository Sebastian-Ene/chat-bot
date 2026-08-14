"""Describe figures so a chart's contents become searchable text.

A figure that carries no caption and no description contributes **nothing** to
the index: Docling merges pictures into surrounding prose, so with nothing to
merge the chart is dropped and its numbers are unreachable. Two golden questions
exist only inside charts (`qa-005`, `qa-007`), and both fail without this stage.

The description is written to `PictureItem.meta`, which `contextualize()` folds
into the chunk text — so it reaches both what is embedded and what the LLM
eventually reads.

**Transcription, not captioning.** "A line chart of battery retention" answers
nothing; the value `qa-005` needs is a point on a line, never text anywhere in
the document. The prompt therefore asks for each series and its value at every
labelled position.

Transport is Docling's own API describer path — `PictureDescriptionApiOptions`
plus `api_image_request` — pointed at Anthropic's OpenAI-compatible endpoint.
Docling's *built-in* enrichment is PDF-only, so driving the request ourselves is
what lets DOCX and HTML figures be described too.
"""
import hashlib
import json
import logging
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from docling.datamodel.pipeline_options import PictureDescriptionApiOptions
from docling.utils.api_image_request import api_image_request
from docling_core.types.doc.document import DoclingDocument, PictureItem
from PIL import Image

from common.logging_config import INGEST_LOGGER
from ingestion.config import get_settings

logger = logging.getLogger(INGEST_LOGGER)

# Anthropic's OpenAI-compatibility layer. Docling's request builder emits the
# OpenAI chat-completions shape (`content[].image_url.url` as a data URI) and
# parses `choices[0].message.content`; the native Messages API accepts neither.
ANTHROPIC_OPENAI_URL = "https://api.anthropic.com/v1/chat/completions"

PROMPT = (
    "Describe this figure so that its contents can be found by a text search. "
    "If it is a chart, list every series by name and give its value at each "
    "labelled position on the x-axis, and state the units. If it is a diagram, "
    "name every labelled element and how they connect. Write in the same "
    "language as the labels in the figure. Give the description only, with no "
    "preamble."
)

_IMG_SRC = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)


@dataclass
class DescribeReport:
    """What the stage did for one document, for the run summary."""

    described: int = 0
    cached: int = 0
    skipped: int = 0


class _Cache:
    """Image hash → description, persisted as JSON.

    Keyed by the bytes rather than the document, so the same figure reused
    across documents — and every re-ingestion — costs one API call in total.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self._entries: dict[str, str] = {}
        if path.exists():
            try:
                self._entries = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                # A corrupt cache must not stop a run; it costs API calls, not
                # correctness.
                logger.warning("unreadable description cache %s: %s", path, error)

    def get(self, key: str) -> str | None:
        return self._entries.get(key)

    def put(self, key: str, description: str) -> None:
        self._entries[key] = description
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._entries, indent=2, ensure_ascii=False), encoding="utf-8"
        )


def html_image_paths(html_path: Path) -> list[Path]:
    """Figure files referenced by an HTML document, in document order.

    Docling populates `PictureItem.image` for PDF and DOCX but **not** HTML, so
    the bytes have to come from disk. `<img src>` is relative to the document.
    """
    try:
        markup = html_path.read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        logger.warning("cannot read %s for figure sources: %s", html_path, error)
        return []
    return [(html_path.parent / src).resolve() for src in _IMG_SRC.findall(markup)]


def _image_for(picture: PictureItem, document: DoclingDocument, fallbacks: list[Path], index: int) -> Image.Image | None:
    """The figure's pixels, from Docling if it has them or from disk if not."""
    image = picture.get_image(document)
    if image is not None:
        return image
    if index < len(fallbacks) and fallbacks[index].is_file():
        try:
            return Image.open(BytesIO(fallbacks[index].read_bytes()))
        except (OSError, ValueError) as error:
            logger.warning("unreadable figure %s: %s", fallbacks[index], error)
    return None


def _hash(image: Image.Image) -> str:
    buffer = BytesIO()
    image.convert("RGB").save(buffer, "PNG")
    return hashlib.sha256(buffer.getvalue()).hexdigest()


def _write(picture: PictureItem, text: str) -> None:
    """Put the description where `contextualize()` will read it.

    `PictureItem.meta` is the supported home; `annotations` is deprecated in
    docling-core 2.91 but still works, so it is the fallback rather than a hard
    dependency on one library version.
    """
    try:
        from docling_core.types.doc.common.meta import DescriptionMetaField
        from docling_core.types.doc.items.picture.meta import PictureMeta

        picture.meta = PictureMeta(
            description=DescriptionMetaField(text=text, created_by="ingestion.describe")
        )
    except ImportError:  # pragma: no cover - depends on docling-core version
        from docling_core.types.doc.document import PictureDescriptionData

        picture.annotations.append(
            PictureDescriptionData(kind="description", text=text, provenance="ingestion.describe")
        )


def describe_pictures(document: DoclingDocument, source: Path, doc_id: str) -> DescribeReport:
    """Describe every figure in a parsed document, in place.

    Never raises: a figure that cannot be described is logged and skipped, and
    the document indexes without it — the same degradation as a failed OCR. A
    missing API key skips the whole stage quietly, so ingestion still runs for
    anyone who has not set one.
    """
    report = DescribeReport()
    if not document.pictures:
        return report

    settings = get_settings()
    cache = _Cache(settings.description_cache)
    fallbacks = html_image_paths(source) if source.suffix.lower() in {".html", ".htm"} else []
    key = settings.anthropic_api_key

    options = PictureDescriptionApiOptions(
        url=ANTHROPIC_OPENAI_URL,
        headers={"Authorization": f"Bearer {key.get_secret_value()}"} if key else {},
        params={"model": settings.describe_model, "max_tokens": settings.describe_max_tokens},
        prompt=PROMPT,
        timeout=60,
    )

    for index, picture in enumerate(document.pictures):
        image = _image_for(picture, document, fallbacks, index)
        if image is None:
            logger.warning("no image bytes for figure %d of %s — skipped", index, doc_id)
            report.skipped += 1
            continue

        digest = _hash(image)
        if description := cache.get(digest):
            _write(picture, description)
            report.cached += 1
            continue

        if key is None:
            logger.warning(
                "no ANTHROPIC_API_KEY — figure %d of %s indexed without a description",
                index,
                doc_id,
            )
            report.skipped += 1
            continue

        try:
            result = api_image_request(
                image=image,
                prompt=options.prompt,
                url=options.url,
                timeout=options.timeout,
                headers=options.headers,
                **options.params,
            )
            description = (result.text or "").strip()
        except Exception as error:
            # Per-figure, never per-document: one unreachable API call must not
            # cost a document its prose.
            logger.warning("describe failed for figure %d of %s: %s", index, doc_id, error)
            report.skipped += 1
            continue

        if not description:
            logger.warning("empty description for figure %d of %s", index, doc_id)
            report.skipped += 1
            continue

        cache.put(digest, description)
        _write(picture, description)
        report.described += 1

    logger.info(
        "described %s figures=%d generated=%d cached=%d skipped=%d",
        doc_id,
        len(document.pictures),
        report.described,
        report.cached,
        report.skipped,
    )
    return report
