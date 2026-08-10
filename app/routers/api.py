import logging
from collections.abc import AsyncIterator
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from app.logging_config import APP_LOGGER
from app.rag.llm import stream_completion
from app.rag.retriever import retrieve
from app.timings import create_timings

router = APIRouter(prefix="/api")

logger = logging.getLogger(APP_LOGGER)

# Conversation history is stateless: the client sends prior turns, so the whole
# history is caller-supplied and every turn is validated, not just the latest
# (requirements.md §6.4). Caps bound cost and context growth.
MAX_HISTORY_TURNS = 10
MAX_HISTORY_CHARS = 10_000
MAX_TURN_CHARS = 4_000


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_TURN_CHARS)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("turn content must not be blank")
        return stripped


class ChatRequest(BaseModel):
    message: str = Field(min_length=5, max_length=300)
    history: list[Turn] = Field(default_factory=list, max_length=MAX_HISTORY_TURNS)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("message must not be blank")
        return stripped

    @field_validator("history")
    @classmethod
    def history_must_start_with_a_user_turn(cls, turns: list[Turn]) -> list[Turn]:
        """The Messages API requires the first message to be `user`. Rejecting
        here turns a forged history into our 422 rather than Anthropic's 400."""
        if turns and turns[0].role != "user":
            raise ValueError("history must start with a user turn")
        return turns

    @field_validator("history")
    @classmethod
    def history_must_be_within_total_length(cls, turns: list[Turn]) -> list[Turn]:
        total = sum(len(turn.content) for turn in turns)
        if total > MAX_HISTORY_CHARS:
            raise ValueError(f"history must not exceed {MAX_HISTORY_CHARS} characters")
        return turns


async def _generate_reply(query: str, history: list[Turn]) -> AsyncIterator[str]:
    timings = create_timings()

    with timings.stage("retrieval"):
        context = await retrieve(query)

    with timings.stage("generation"):
        async for chunk in stream_completion(
            query, context, history=[turn.model_dump() for turn in history]
        ):
            timings.mark_first_token()
            yield chunk

    logger.info(
        "chat request completed message_length=%d chunks=%d history_turns=%d",
        len(query),
        len(context),
        len(history),
    )
    timings.log(message_length=len(query), history_turns=len(history))


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    logger.info(
        "chat request received message_length=%d history_turns=%d",
        len(request.message),
        len(request.history),
    )
    return StreamingResponse(
        _generate_reply(request.message, request.history), media_type="text/plain"
    )
