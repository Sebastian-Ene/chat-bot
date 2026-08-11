"""Spike 1 — can we get image bytes out of Docling for DOCX and HTML, or PDF only?

Why it matters: the design generates captions for figures that carry none
(requirements §6.1). That needs the image itself. Docling's *own* picture
description enrichment is PDF-only, and it is not obvious whether
`PictureItem.image` is populated for the other two backends.

If DOCX/HTML yield no bytes, caption generation cannot run for two of three
formats and the design has to change.

    uv run python -m scripts.spikes.docling_pictures
"""
import os
from pathlib import Path

# torch tries to JIT-compile through inductor/triton, which needs a C compiler.
# There isn't one in this environment, and ingest is offline anyway, so the
# eager path is fine. Must be set before torch is imported.
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")

from docling.datamodel.base_models import InputFormat  # noqa: E402
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

SAMPLES = [
    Path("corpus/docs-initial/coverage/aurora-installation-guide-en.pdf"),  # PDF, captioned
    Path("corpus/docs-initial/coverage/aurora-technische-daten-de.pdf"),  # PDF, uncaptioned
    Path("corpus/docs-initial/coverage/aurora-support-faq.html"),  # HTML, uncaptioned
    Path("corpus/docs-initial/bulk/energiebericht-de.pdf"),  # PDF, captioned
    Path("corpus/docs-initial/bulk/accessory-catalogue-en.docx"),  # DOCX, captioned
    Path("corpus/docs-initial/bulk/troubleshooting-zeitplan-de.docx"),  # DOCX, uncaptioned
]


def _converter() -> DocumentConverter:
    options = PdfPipelineOptions()
    options.do_ocr = True
    options.do_table_structure = True
    # Without this Docling discards page/figure images after parsing.
    options.generate_picture_images = True
    options.images_scale = 2.0
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )


def main() -> None:
    converter = _converter()

    for path in SAMPLES:
        if not path.exists():
            print(f"\n=== {path} — MISSING, skipped")
            continue

        print(f"\n=== {path.name} ({path.suffix})")
        result = converter.convert(str(path))
        doc = result.document

        pictures = list(doc.pictures)
        tables = list(doc.tables)
        print(f"    pages={len(doc.pages)} pictures={len(pictures)} tables={len(tables)}")

        for index, picture in enumerate(pictures):
            caption_text = picture.caption_text(doc=doc) if hasattr(picture, "caption_text") else ""

            image_ref = getattr(picture, "image", None)
            pil = None
            if hasattr(picture, "get_image"):
                try:
                    pil = picture.get_image(doc)
                except Exception as error:  # noqa: BLE001 — spike: report, don't raise
                    pil = f"get_image failed: {type(error).__name__}: {error}"

            size = getattr(pil, "size", None) if not isinstance(pil, str) else None
            print(
                f"    picture[{index}] caption={caption_text[:60]!r} "
                f"image_ref={'yes' if image_ref is not None else 'no'} "
                f"get_image={'PIL ' + str(size) if size else pil}"
            )
            print(f"      annotations={getattr(picture, 'annotations', None)}")


if __name__ == "__main__":
    main()
