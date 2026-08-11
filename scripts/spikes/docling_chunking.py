"""Spike 2 — how does a picture reach the chunker?

Two questions the design depends on:

1. Does `HybridChunker` emit pictures at all, or do figures vanish at chunking?
2. Does `contextualize()` include a picture's `annotations`? That decides *where*
   a generated caption has to be written back for it to be indexed.

Also samples what a table chunk looks like, since table-only answers are a third
of the golden set.

    uv run python -m scripts.spikes.docling_chunking
"""
import os
from pathlib import Path

# See docling_pictures.py — no C compiler here, so keep torch off the JIT path.
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")

from docling.document_converter import DocumentConverter  # noqa: E402
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker  # noqa: E402

SAMPLE = Path("corpus/docs-initial/coverage/aurora-technische-daten-de.pdf")
TOKENIZER = "BAAI/bge-m3"
MAX_TOKENS = 512


def main() -> None:
    print(f"converting {SAMPLE}")
    doc = DocumentConverter().convert(str(SAMPLE)).document

    print(f"pictures in document: {len(doc.pictures)}")

    # Write a marker into the first picture's annotations, then check whether it
    # survives into a chunk — that is the write-back question.
    marker = "SPIKE_MARKER_generated_caption"
    if doc.pictures:
        picture = doc.pictures[0]
        # `annotations` still works but is deprecated in docling-core 2.91 in
        # favour of `meta`. Prefer the supported field, and fall back so the
        # spike still reports something if the new shape rejects us.
        try:
            from docling_core.types.doc.common.meta import DescriptionMetaField
            from docling_core.types.doc.items.picture.meta import PictureMeta

            # `created_by` is the natural home for caption provenance
            # (extracted / generated + which model produced it).
            picture.meta = PictureMeta(
                description=DescriptionMetaField(text=marker, created_by="spike")
            )
            print("description written via PictureMeta.description")
        except Exception as error:  # noqa: BLE001 — spike: report, don't raise
            print(f"PictureMeta path failed: {type(error).__name__}: {error}")
            from docling_core.types.doc.document import PictureDescriptionData

            picture.annotations.append(
                PictureDescriptionData(kind="description", text=marker, provenance="spike")
            )
            print("fell back to deprecated annotations")

    chunker = HybridChunker(tokenizer=TOKENIZER, max_tokens=MAX_TOKENS)
    chunks = list(chunker.chunk(dl_doc=doc))
    print(f"\nchunks: {len(chunks)}")

    marker_hits = 0
    kinds: dict[str, int] = {}
    for index, chunk in enumerate(chunks):
        items = getattr(chunk.meta, "doc_items", [])
        labels = sorted({str(getattr(item, "label", "?")) for item in items})
        for label in labels:
            kinds[label] = kinds.get(label, 0) + 1

        contextualized = chunker.contextualize(chunk=chunk)
        if marker in contextualized:
            marker_hits += 1

        if index < 6 or marker in contextualized:
            headings = getattr(chunk.meta, "headings", None)
            print(f"\n-- chunk[{index}] labels={labels} headings={headings}")
            print(f"   raw       : {chunk.text[:160]!r}")
            print(f"   contextual: {contextualized[:220]!r}")

    print(f"\nlabel histogram across chunks: {kinds}")
    print(f"chunks containing the picture annotation marker: {marker_hits}")
    print(
        "\nVERDICT: pictures reach the chunker"
        if any("picture" in label.lower() for label in kinds)
        else "\nVERDICT: no picture-labelled chunk was emitted"
    )


if __name__ == "__main__":
    main()
