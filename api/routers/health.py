"""Liveness probe.

Deliberately unauthenticated and trivial: the container HEALTHCHECK used to
probe `/`, which renders the chat template and mints a JWT on every check. This
answers the same question without doing any of that work.

It reports that the process is up and serving, nothing more — Qdrant
connectivity and the embedder are checked once at startup (see `api/main.py`),
and a failure there stops the app from serving at all.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
