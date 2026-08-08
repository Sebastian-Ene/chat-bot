from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import api, pages

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="chat-bot")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(pages.router)
app.include_router(api.router)
