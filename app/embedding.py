"""BGE-M3 embedding, shared by the ingest job and the api.

Index-time and query-time embeddings must come from the same model with the
same settings — a query embedded differently from the chunks it should match
simply does not retrieve them, and nothing about the failure looks like a bug.
That is why this module is shared rather than duplicated per service, and why
the model name lives in settings rather than at either call site.

Dense and sparse come out of one forward pass, so hybrid retrieval costs one
model rather than two. Sparse weights are BGE-M3's own learned lexical weights,
not BM25 — the same model decides both halves.
"""
import logging
import os
from dataclasses import dataclass
from functools import lru_cache

# torch JIT-compiles through inductor/triton, which needs a C compiler that is
# not present in the container. Must be set before torch is imported.
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")

from FlagEmbedding import BGEM3FlagModel  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.logging_config import APP_LOGGER  # noqa: E402

logger = logging.getLogger(APP_LOGGER)


@dataclass(frozen=True)
class Embedding:
    """One text's vectors. `sparse` maps token id to learned weight."""

    dense: list[float]
    sparse: dict[int, float]

    def sparse_indices_and_values(self) -> tuple[list[int], list[float]]:
        """Qdrant wants two parallel arrays rather than a mapping."""
        if not self.sparse:
            return [], []
        items = sorted(self.sparse.items())
        return [index for index, _ in items], [value for _, value in items]


@lru_cache(maxsize=1)
def get_embedder() -> BGEM3FlagModel:
    """Loaded once per process — several GB of weights."""
    settings = get_settings()
    logger.info("loading embedding model %s", settings.embedding_model)
    model = BGEM3FlagModel(
        settings.embedding_model,
        # fp16 is a GPU optimisation; on CPU it is slower and less accurate.
        use_fp16=False,
        # Normalised vectors let Qdrant's cosine distance work as a dot product.
        normalize_embeddings=True,
        # FlagEmbedding truncates at 512 by default, which would silently cut
        # the chunks whose heading path pushes them past the chunk budget — the
        # tail would be embedded as if it did not exist. BGE-M3 itself accepts
        # 8192; this only needs to clear the longest contextualised chunk.
        passage_max_length=settings.embed_max_tokens,
        query_max_length=settings.embed_max_tokens,
    )
    logger.info("embedding model ready")
    return model


def _to_embeddings(output) -> list[Embedding]:
    """FlagEmbedding returns numpy arrays and string-keyed sparse weights."""
    dense_vectors = output["dense_vecs"]
    lexical_weights = output["lexical_weights"]
    return [
        Embedding(
            dense=[float(value) for value in dense],
            # Token ids arrive as strings; Qdrant needs integer indices.
            sparse={int(token): float(weight) for token, weight in sparse.items()},
        )
        for dense, sparse in zip(dense_vectors, lexical_weights, strict=True)
    ]


def embed_documents(texts: list[str]) -> list[Embedding]:
    """Embed chunk texts for indexing."""
    if not texts:
        return []

    settings = get_settings()
    output = get_embedder().encode(
        texts,
        batch_size=settings.embed_batch_size,
        return_dense=True,
        return_sparse=True,
        return_colbert_vecs=False,
    )
    embeddings = _to_embeddings(output)
    logger.debug("embedded %d documents", len(embeddings))
    return embeddings


def embed_query(text: str) -> Embedding:
    """Embed one query.

    Separate from `embed_documents` so the api has a call that cannot be handed
    a batch with different settings — BGE-M3 needs no asymmetric prefix, but the
    two sides must stay identical, and one shared function invites drift.
    """
    output = get_embedder().encode(
        [text],
        return_dense=True,
        return_sparse=True,
        return_colbert_vecs=False,
    )
    return _to_embeddings(output)[0]
