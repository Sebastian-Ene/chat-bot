"""Hybrid retrieval over the indexed corpus.

Every populated query branch is searched on **both** vector kinds — dense for
meaning, sparse for exact terms like `F250` — and Qdrant fuses all of it
server-side with RRF in a single request. The original query always contributes
a branch, so a rewrite that drifts cannot retrieve worse than the raw question.

Retrieval failing is not a 500. If Qdrant is unreachable or the corpus was never
ingested, this returns nothing and the generator says it cannot answer — a
degraded reply beats a broken chat.
"""
import logging
from dataclasses import dataclass, field

import anyio
from qdrant_client import models

from common import vector_store
from api.core.config import get_settings
from common.embedding import Embedding, embed_documents
from common.logging_config import APP_LOGGER, truncate
from common.vector_store import DENSE_VECTOR, SPARSE_VECTOR

logger = logging.getLogger(APP_LOGGER)


@dataclass(frozen=True)
class RetrievalQueries:
    """What retrieval searches on.

    Defined here rather than reusing `QueryAnalysis`: that model also carries the
    safety verdict, which retrieval has no business seeing. The orchestrator maps
    one to the other.

    Each populated field becomes its own `prefetch` branch, fused with RRF
    (requirements.md §6.2, §6.4). `original` always survives fusion, so a rewrite
    that drifts cannot retrieve worse than the raw query alone.
    """

    original: str
    rewritten: str = ""
    # Populated once the rewrite produces them; both are behind config flags.
    keywords: tuple[str, ...] = field(default_factory=tuple)
    sub_queries: tuple[str, ...] = field(default_factory=tuple)

    def branches(self) -> list[str]:
        """Names of the branches that will actually be searched — for the trace."""
        names = ["original"]
        if self.rewritten:
            names.append("rewritten")
        if self.keywords:
            names.append("keywords")
        names.extend(f"sub_query[{index}]" for index in range(len(self.sub_queries)))
        return names

    def texts(self) -> list[str]:
        """The text each branch searches on, in `branches()` order."""
        texts = [self.original]
        if self.rewritten:
            texts.append(self.rewritten)
        if self.keywords:
            # One branch, not one per keyword: they describe a single query.
            texts.append(" ".join(self.keywords))
        texts.extend(self.sub_queries)
        return texts


@dataclass(frozen=True)
class RetrievedChunk:
    """A chunk that matched, with the provenance an answer needs to cite it."""

    text: str
    doc_id: str
    chunk_index: int
    score: float
    source_format: str = ""
    parent_id: str = ""
    headings: list[str] = field(default_factory=list)
    page_numbers: list[int] = field(default_factory=list)

    @classmethod
    def from_point(cls, point) -> "RetrievedChunk":
        payload = point.payload or {}
        return cls(
            text=payload.get("text", ""),
            doc_id=payload.get("doc_id", ""),
            chunk_index=payload.get("chunk_index", -1),
            score=point.score,
            source_format=payload.get("source_format", ""),
            parent_id=payload.get("parent_id", ""),
            headings=payload.get("headings") or [],
            page_numbers=payload.get("page_numbers") or [],
        )

    def citation(self) -> str:
        """Human-readable provenance, for the logs. Answers carry no citations."""
        pages = (
            f" p.{','.join(str(page) for page in self.page_numbers)}"
            if self.page_numbers
            else ""
        )
        return f"{self.doc_id}{pages}"


def _prefetch(embeddings: list[Embedding], limit: int) -> list[models.Prefetch]:
    """One dense and one sparse branch per query text.

    Both kinds for every branch: dense carries meaning across languages, sparse
    keeps exact tokens — an error code has to survive as a term, not be smeared
    into a topic vector.
    """
    branches = []
    for embedding in embeddings:
        indices, values = embedding.sparse_indices_and_values()
        branches.append(
            models.Prefetch(query=embedding.dense, using=DENSE_VECTOR, limit=limit)
        )
        if indices:
            branches.append(
                models.Prefetch(
                    query=models.SparseVector(indices=indices, values=values),
                    using=SPARSE_VECTOR,
                    limit=limit,
                )
            )
    return branches


async def retrieve(queries: RetrievalQueries) -> list[RetrievedChunk]:
    """Search every branch and return the fused top chunks."""
    settings = get_settings()
    texts = queries.texts()

    # One batched forward pass for every branch, rather than one call each.
    # Embedding is CPU-bound and synchronous, so it goes off the event loop.
    embeddings = await anyio.to_thread.run_sync(embed_documents, texts)

    try:
        response = await anyio.to_thread.run_sync(
            lambda: vector_store.get_client().query_points(
                collection_name=settings.qdrant_collection,
                prefetch=_prefetch(embeddings, settings.retrieval_prefetch_limit),
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=settings.retrieval_top_k,
                with_payload=True,
            )
        )
    except Exception as error:
        # Degrade, don't fail: the generator will say it cannot answer.
        logger.error(
            "retrieval failed, answering without context: %s: %s",
            type(error).__name__,
            error,
        )
        return []

    chunks = [RetrievedChunk.from_point(point) for point in response.points]
    logger.debug(
        "retrieved branches=%s chunks=%d sources=%s",
        queries.branches(),
        len(chunks),
        truncate(", ".join(chunk.citation() for chunk in chunks)),
    )
    return chunks
