from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import vector_store
from app.config import get_settings
from app.logging_config import configure_logging
from app.routers import api, pages

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    get_settings()  # fail fast on missing or invalid configuration
    configure_logging()
    vector_store.check_connection()  # fail fast if the vector store is unreachable
    yield


app = FastAPI(title="chat-bot", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(pages.router)
app.include_router(api.router)
