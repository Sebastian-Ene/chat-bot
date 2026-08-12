"""The ingester's HTTP surface.

Deliberately tiny. It exists so the ingestion run can be triggered after
documents are dropped into the corpus directory, and it is reachable only on the
internal network — never published to the host.

The pipeline itself is not built yet, so `POST /ingest` answers 501 rather than
accepting work it cannot do.
"""
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

# Docling pulls torch, which tries to JIT-compile through inductor/triton and
# needs a C compiler. Must be set before torch is imported anywhere.
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")

from fastapi import FastAPI, HTTPException, status  # noqa: E402

from app import vector_store  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.logging_config import INGEST_LOGGER, configure_logging  # noqa: E402

logger = logging.getLogger(INGEST_LOGGER)

DOCUMENT_SUFFIXES = {".pdf", ".docx", ".html"}


def count_documents() -> int:
    """Documents visible under the corpus root, at any depth."""
    root = get_settings().corpus_dir
    if not root.is_dir():
        return 0
    return sum(1 for path in root.rglob("*") if path.suffix.lower() in DOCUMENT_SUFFIXES)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging("ingest")
    vector_store.check_connection()  # same fail-fast contract as the api

    root = settings.corpus_dir
    logger.info(
        "ingester ready corpus_dir=%s exists=%s documents=%d",
        root,
        root.is_dir(),
        count_documents(),
    )
    yield


service = FastAPI(title="chat-bot ingester", lifespan=lifespan)


@service.get("/health")
def health() -> dict:
    """Also reports what the corpus mount looks like from in here, so a broken
    volume shows up as data rather than as an empty ingestion run."""
    root = get_settings().corpus_dir
    return {
        "status": "ok",
        "corpus_dir": str(root),
        "corpus_mounted": root.is_dir(),
        "documents": count_documents(),
    }


@service.post("/ingest", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def ingest() -> None:
    """Not built yet. Answering 501 rather than a hollow 202 — a stub that
    claims to have accepted work is worse than one that admits it cannot."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="ingestion pipeline not implemented yet",
    )
