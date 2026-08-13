"""Splitting a parsed document into the units that get embedded and retrieved.

Chunk boundaries are measured with **BGE-M3's own tokenizer**, not a default
one: a chunk sized in someone else's tokens is not 512 tokens to the embedder,
and the overflow is silent — the tail is simply truncated at embed time and
never retrievable.

Each chunk carries two texts. `embed_text` is Docling's contextualised form,
which prepends the heading path, so a chunk reading "Reset the hub" is findable
as belonging to *Troubleshooting → Hub offline*. `text` is the raw chunk, which
is what reaches the LLM and the citation — putting synthetic heading
breadcrumbs into the prompt would put them into the answer.

Note the budget applies to the **raw** chunk: Docling sizes a chunk on its own
serialisation and only then prepends the heading path, so `embed_text` can run
past `chunk_max_tokens` by the length of that path. On this corpus 27 of 207
chunks do, by at most 7 tokens. Harmless — BGE-M3 accepts 8192, so nothing is
truncated — but downstream code must not assume the budget holds for
`embed_text`.
"""
import logging
import os
from dataclasses import dataclass, field
from functools import lru_cache

# Docling pulls torch, which tries to JIT-compile through inductor/triton and
# needs a C compiler. Must be set before torch is imported anywhere.
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")

from docling_core.transforms.chunker.hybrid_chunker import HybridChunker  # noqa: E402
from docling_core.transforms.chunker.tokenizer.huggingface import (  # noqa: E402
    HuggingFaceTokenizer,
)

from ingestion.config import get_settings  # noqa: E402
from common.logging_config import INGEST_LOGGER  # noqa: E402
from ingestion.parse import ParsedDocument  # noqa: E402

logger = logging.getLogger(INGEST_LOGGER)


@dataclass(frozen=True)
class Chunk:
    """One retrievable unit, with everything needed to cite it."""

    doc_id: str
    doc_content_hash: str
    chunk_index: int
    text: str
    embed_text: str
    source_format: str
    headings: list[str] = field(default_factory=list)
    page_numbers: list[int] = field(default_factory=list)
    # The section this chunk belongs to. Neighbour expansion clamps its window
    # to it, so a chunk from the next section cannot be pulled in as context and
    # mislead grounding. Docling exposes no section id, so the heading path
    # stands in for one — same path, same section.
    parent_id: str = ""


def _parent_id(doc_id: str, headings: list[str]) -> str:
    """Identify the section a chunk sits in.

    Scoped by `doc_id`: without it, the "Introduction" of fifteen different
    documents would share one parent_id and expansion could treat unrelated
    documents as one section.
    """
    return f"{doc_id}#{' > '.join(headings)}"


@lru_cache(maxsize=1)
def get_chunker() -> HybridChunker:
    """Built once per process — it loads a tokenizer."""
    settings = get_settings()
    tokenizer = HuggingFaceTokenizer.from_pretrained(
        model_name=settings.embedding_model,
        max_tokens=settings.chunk_max_tokens,
    )
    logger.info(
        "chunker ready tokenizer=%s max_tokens=%d",
        settings.embedding_model,
        settings.chunk_max_tokens,
    )
    # repeat_table_header and merge_peers are on by default: a table split across
    # chunks keeps its header row, and undersized neighbours are merged.
    return HybridChunker(tokenizer=tokenizer)


def _page_numbers(doc_chunk) -> list[int]:
    """Pages this chunk came from, deduplicated and ordered.

    Empty for DOCX and HTML — only PDF carries page provenance, so a citation
    format has to tolerate a chunk without a page rather than treat it as an
    error.
    """
    pages = {
        prov.page_no
        for item in doc_chunk.meta.doc_items
        for prov in item.prov
        if prov.page_no is not None
    }
    return sorted(pages)


def chunk(parsed: ParsedDocument) -> list[Chunk]:
    """Split one parsed document. An empty document yields no chunks."""
    chunker = get_chunker()
    chunks = []
    for index, doc_chunk in enumerate(chunker.chunk(parsed.document)):
        headings = list(doc_chunk.meta.headings or [])
        chunks.append(
            Chunk(
                doc_id=parsed.doc_id,
                doc_content_hash=parsed.content_hash,
                chunk_index=index,
                text=doc_chunk.text,
                embed_text=chunker.contextualize(doc_chunk),
                source_format=parsed.source_format,
                headings=headings,
                page_numbers=_page_numbers(doc_chunk),
                parent_id=_parent_id(parsed.doc_id, headings),
            )
        )

    logger.debug(
        "chunked %s chunks=%d pages_covered=%d",
        parsed.doc_id,
        len(chunks),
        len({page for chunk_ in chunks for page in chunk_.page_numbers}),
    )
    return chunks


