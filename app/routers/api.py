import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from app.logging_config import APP_LOGGER
from app.rag.llm import stream_completion
from app.rag.retriever import retrieve
from app.timings import create_timings

router = APIRouter(prefix="/api")

logger = logging.getLogger(APP_LOGGER)


class ChatRequest(BaseModel):
    message: str = Field(min_length=5, max_length=300)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("message must not be blank")
        return stripped


async def _generate_reply(query: str) -> AsyncIterator[str]:
    timings = create_timings()

    with timings.stage("retrieval"):
        context = await retrieve(query)

    with timings.stage("generation"):
        async for chunk in stream_completion(query, context):
            timings.mark_first_token()
            yield chunk

    logger.info("chat request completed message_length=%d chunks=%d", len(query), len(context))
    timings.log(message_length=len(query))


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    logger.info("chat request received message_length=%d", len(request.message))
    return StreamingResponse(_generate_reply(request.message), media_type="text/plain")
