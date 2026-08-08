from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from app.rag.llm import stream_completion
from app.rag.retriever import retrieve

router = APIRouter(prefix="/api")


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
    context = await retrieve(query)
    async for chunk in stream_completion(query, context):
        yield chunk


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(_generate_reply(request.message), media_type="text/plain")
