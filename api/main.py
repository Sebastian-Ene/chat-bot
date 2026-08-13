from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.core.config import ApiSettings
from api.core.constants import STATIC_DIR
from api.routers import api, health, pages
from common import vector_store
from common.config import configure
from common.embedding import get_embedder
from common.logging_config import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # First, and before anything reads configuration: `common/` has no settings
    # of its own and serves whichever child the entrypoint injects. Building
    # ApiSettings here also fails fast on missing or invalid configuration.
    configure(ApiSettings())
    configure_logging("api")
    vector_store.check_connection()  # fail fast if the vector store is unreachable
    # Load BGE-M3 now rather than on the first search. The weights are baked into
    # the image, but loading them still takes seconds — paid once at startup here
    # instead of by whoever asks the first question. Off the event loop, since it
    # is CPU-bound.
    await anyio.to_thread.run_sync(get_embedder)
    yield


app = FastAPI(title="chat-bot", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(pages.router)
app.include_router(health.router)
app.include_router(api.router)
