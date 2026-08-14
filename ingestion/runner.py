"""The ingestion run: discover, plan, then each document end to end.

Ingestion is a batch job, not a service. It runs to completion, it is started by
an operator or a schedule, and it takes minutes — so it is a callable with a
report, invoked from `python -m ingestion`, rather than a request handler.

Documents are processed **one at a time, all the way through**: parse, chunk,
embed, index. Holding every parsed document and every embedding in memory before
writing anything would grow with the corpus for no benefit, and it would put the
whole run at the mercy of one bad file. This way a failure costs exactly one
document, and the run says which one.
"""
import logging
import os
from dataclasses import dataclass, field
from time import perf_counter

# Docling pulls torch, which tries to JIT-compile through inductor/triton and
# needs a C compiler. Must be set before torch is imported anywhere.
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")

from qdrant_client import QdrantClient  # noqa: E402

from common import vector_store  # noqa: E402
from ingestion.config import get_settings  # noqa: E402
from common.embedding import embed_documents  # noqa: E402
from common.logging_config import INGEST_LOGGER  # noqa: E402
from ingestion.chunk import chunk  # noqa: E402
from ingestion.describe import describe_pictures  # noqa: E402
from ingestion.discovery import DiscoveredDocument, discover  # noqa: E402
from ingestion.index import delete_documents, delete_stale, index_document  # noqa: E402
from ingestion.parse import parse  # noqa: E402
from ingestion.state import IngestPlan, build_plan  # noqa: E402

logger = logging.getLogger(INGEST_LOGGER)


class DocumentFailed(Exception):
    """A document could not be ingested. Names the stage that gave up."""


@dataclass(frozen=True)
class RunReport:
    """What a run actually did. `failed` carries doc_ids, not counts, so the
    summary can name them — a count alone is not actionable."""

    discovered: int = 0
    plan: IngestPlan = field(default_factory=IngestPlan)
    indexed: int = 0
    chunks_indexed: int = 0
    points_deleted: int = 0
    failed: list[str] = field(default_factory=list)
    seconds: float = 0.0
    dry_run: bool = False

    @property
    def ok(self) -> bool:
        return not self.failed

    def summary(self) -> str:
        if self.dry_run:
            return f"dry run: discovered={self.discovered} {self.plan.summary()} (nothing written)"
        line = (
            f"discovered={self.discovered} {self.plan.summary()} "
            f"indexed={self.indexed} chunks={self.chunks_indexed} "
            f"deleted_points={self.points_deleted} failed={len(self.failed)} "
            f"seconds={self.seconds:.1f}"
        )
        if self.failed:
            line += f" failed_docs={','.join(self.failed)}"
        return line


def ingest_document(client: QdrantClient, document: DiscoveredDocument) -> int:
    """Take one document from file to indexed chunks. Returns chunks written.

    Raises `DocumentFailed` naming the stage, so the caller can skip this
    document and the log says what to fix.
    """
    stage = "parse"
    try:
        parsed = parse(document)

        # Before chunking: a description on the picture is folded into the
        # chunk text, and a figure with neither caption nor description is
        # dropped entirely.
        stage = "describe"
        described = describe_pictures(parsed.document, document.path, document.doc_id)

        stage = "chunk"
        chunks = chunk(parsed)
        if not chunks:
            # Not a failure: some documents legitimately hold nothing chunkable.
            logger.warning("no chunks produced, nothing to index: %s", document.doc_id)
            return 0

        stage = "embed"
        embeddings = embed_documents([c.embed_text for c in chunks])

        stage = "index"
        written = index_document(client, chunks, embeddings)

        stage = "delete_stale"
        delete_stale(client, document.doc_id, document.content_hash)
    except Exception as error:
        raise DocumentFailed(
            f"{document.doc_id}: {stage}: {type(error).__name__}: {error}"
        ) from error

    logger.info(
        "ingested %s chunks=%d pages=%d tables=%d pictures=%d described=%d cached=%d",
        document.doc_id,
        written,
        parsed.page_count,
        parsed.table_count,
        parsed.picture_count,
        described.described,
        described.cached,
    )
    return written


def run(client: QdrantClient, *, force: bool = False, dry_run: bool = False) -> RunReport:
    """Execute one ingestion run over the configured corpus root.

    `force` re-processes every discovered document regardless of the plan, for
    when the pipeline itself changed and the hashes cannot know it. `dry_run`
    reports the plan and stops before anything is written.
    """
    started = perf_counter()
    root = get_settings().corpus_dir

    logger.info("ingestion run starting corpus_dir=%s force=%s dry_run=%s", root, force, dry_run)
    discovered = discover(root)
    plan = build_plan(client, discovered)

    if dry_run:
        report = RunReport(discovered=len(discovered), plan=plan, dry_run=True)
        logger.info("ingestion run finished %s", report.summary())
        return report

    vector_store.ensure_collection(client)

    to_process = discovered if force else plan.to_index
    if force:
        logger.info("force: re-processing all %d documents, ignoring the plan", len(to_process))

    indexed = 0
    chunks_indexed = 0
    failed: list[str] = []

    for position, document in enumerate(to_process, start=1):
        logger.debug("[%d/%d] %s", position, len(to_process), document.doc_id)
        try:
            chunks_indexed += ingest_document(client, document)
            indexed += 1
        except DocumentFailed as error:
            # Alert on this in production. A document that never ingests is
            # invisible in retrieval and nothing else will report it — the
            # doc_id and stage here are what a retry or a fix starts from.
            logger.error("ingestion failed, skipping document: %s", error)
            failed.append(document.doc_id)

    points_deleted = delete_documents(client, plan.deleted)

    report = RunReport(
        discovered=len(discovered),
        plan=plan,
        indexed=indexed,
        chunks_indexed=chunks_indexed,
        points_deleted=points_deleted,
        failed=failed,
        seconds=round(perf_counter() - started, 2),
    )
    if failed:
        logger.error("%d of %d documents failed: %s", len(failed), len(to_process), ", ".join(failed))
    logger.info("ingestion run finished %s", report.summary())
    return report
