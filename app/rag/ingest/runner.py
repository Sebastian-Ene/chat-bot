"""The ingestion run: discover, plan, parse.

Ingestion is a batch job, not a service. It runs to completion, it is started by
an operator or a schedule, and it takes minutes — so it is a callable with a
report, invoked from `python -m app.rag.ingest`, rather than a request handler.

Indexing and vector deletion are not here yet; they belong to RAG — Store and
land where the TODOs are. Until then a run parses and reports, and the report
says as much rather than implying documents were indexed.
"""
import logging
import os
from dataclasses import dataclass, field
from time import perf_counter

# Docling pulls torch, which tries to JIT-compile through inductor/triton and
# needs a C compiler. Must be set before torch is imported anywhere.
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")

from qdrant_client import QdrantClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.logging_config import INGEST_LOGGER  # noqa: E402
from app.rag.ingest.discovery import discover  # noqa: E402
from app.rag.ingest.parse import parse_all  # noqa: E402
from app.rag.ingest.state import IngestPlan, build_plan  # noqa: E402

logger = logging.getLogger(INGEST_LOGGER)


@dataclass(frozen=True)
class RunReport:
    """What a run actually did. `failed` carries doc_ids, not counts, so the
    summary can name them — a count alone is not actionable."""

    discovered: int = 0
    plan: IngestPlan = field(default_factory=IngestPlan)
    parsed: int = 0
    failed: list[str] = field(default_factory=list)
    seconds: float = 0.0
    dry_run: bool = False

    @property
    def ok(self) -> bool:
        return not self.failed

    def summary(self) -> str:
        if self.dry_run:
            return f"dry run: discovered={self.discovered} {self.plan.summary()} (nothing parsed)"
        line = (
            f"discovered={self.discovered} {self.plan.summary()} "
            f"parsed={self.parsed} failed={len(self.failed)} seconds={self.seconds:.1f}"
        )
        if self.failed:
            line += f" failed_docs={','.join(self.failed)}"
        return line


def run(client: QdrantClient, *, force: bool = False, dry_run: bool = False) -> RunReport:
    """Execute one ingestion run over the configured corpus root.

    `force` re-processes every discovered document regardless of the plan, for
    when the pipeline itself changed and the hashes cannot know it. `dry_run`
    reports the plan and stops before any parsing.
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

    to_parse = discovered if force else plan.to_index
    if force:
        logger.info("force: re-processing all %d documents, ignoring the plan", len(to_parse))

    parsed, failed = parse_all(to_parse)

    # TODO(RAG — Store): chunk, embed and upsert `parsed` in a single upsert per
    # document, then delete the vectors of `plan.deleted`.

    report = RunReport(
        discovered=len(discovered),
        plan=plan,
        parsed=len(parsed),
        failed=failed,
        seconds=round(perf_counter() - started, 2),
    )
    logger.info("ingestion run finished %s", report.summary())
    return report
