from fastapi import FastAPI

from app.routers import pages

app = FastAPI(title="chat-bot")
app.include_router(pages.router)
