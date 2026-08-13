import logging
from collections.abc import AsyncIterator
from typing import Literal

from fastapi import APIRouter, Depends, Response
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator

from app.logging_config import APP_LOGGER, truncate
from app.rag.llm import stream_completion
from app.rag.query_analysis import AnalysisUnavailable, analyse_query
from app.rag.retriever import RetrievalQueries, retrieve
from app.request_context import new_request_id, set_request_id
from app.security import verify_token
from app.timings import create_timings

router = APIRouter(prefix="/api")

logger = logging.getLogger(APP_LOGGER)

# Content decisions, not protocol errors, so both come back as a normal 200.
# Kept distinct: a user who asked something legitimate should not be told they
# did something wrong just because we broke.
REFUSAL_REPLY = "I can't help with that request."
UNAVAILABLE_REPLY = "Sorry — I couldn't process that just now. Please try again."

# The client cannot tell a refusal from an answer by the body alone, and must not
# record a refused exchange into history — otherwise the next request is judged
# against a conversation containing the attack, and one refusal poisons the
# session.
OUTCOME_HEADER = "X-Chat-Outcome"

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


def _headers(request_id: str, outcome: str) -> dict[str, str]:
    # X-Request-ID ties a reply to its log lines; X-Chat-Outcome tells the client
    # whether this exchange belongs in the conversation history.
    return {"X-Request-ID": request_id, OUTCOME_HEADER: outcome}


def _log_completion(outcome: str, query: str, turns: int, timings, chunks: int = 0) -> None:
    logger.info(
        "chat request completed outcome=%s message_length=%d chunks=%d history_turns=%d",
        outcome,
        len(query),
        chunks,
        turns,
    )
    timings.log(message_length=len(query), history_turns=turns, outcome=outcome)


async def _stream_answer(
    query: str,
    turns: list[dict[str, str]],
    analysis,
    request_id: str,
    timings,
) -> AsyncIterator[str]:
    # Re-set inside the generator: it is iterated after the endpoint returns, so
    # this guarantees every downstream stage logs under the same id.
    set_request_id(request_id)

    queries = RetrievalQueries(
        original=query,
        rewritten=analysis.rewritten_query,
        keywords=tuple(analysis.keywords),
        sub_queries=tuple(analysis.sub_queries),
    )

    with timings.stage("retrieval"):
        chunks = await retrieve(queries)

    logger.debug(
        "stage=retrieval branches=%s chunks=%d sources=%s preview=%r",
        ",".join(queries.branches()),
        len(chunks),
        ", ".join(chunk.citation() for chunk in chunks) or "none",
        truncate(" | ".join(chunk.text for chunk in chunks)),
    )

    # TODO(citations): pass the chunks as document blocks instead of flattening
    # to text, so Claude's native citations resolve to a chunk rather than a
    # number the model wrote itself. See docs/work.md, RAG — Generate.
    context = [chunk.text for chunk in chunks]

    reply_chars = 0
    streamed = 0
    with timings.stage("generation"):
        async for chunk in stream_completion(
            query, context, history=turns, on_usage=timings.usage_recorder("generation")
        ):
            timings.mark_first_token()
            reply_chars += len(chunk)
            streamed += 1
            yield chunk

    logger.debug(
        "stage=generation reply_chars=%d chunks_streamed=%d", reply_chars, streamed
    )
    _log_completion("answered", query, len(turns), timings, chunks=len(context))


@router.post("/chat", dependencies=[Depends(verify_token)])
async def chat(request: ChatRequest) -> Response:
    """Analysis runs here rather than inside the generator: response headers are
    sent before the generator is iterated, so the outcome has to be known first.
    """
    request_id = new_request_id()
    set_request_id(request_id)
    logger.info(
        "chat request received message_length=%d history_turns=%d",
        len(request.message),
        len(request.history),
    )

    query = request.message
    turns = [turn.model_dump() for turn in request.history]
    timings = create_timings()
    logger.debug("stage=input message=%r history_turns=%d", truncate(query), len(turns))

    # Safety verdict and query rewrite share one call, before retrieval.
    analysis = None
    with timings.stage("analysis"):
        try:
            analysis = await analyse_query(
                query, turns, on_usage=timings.usage_recorder("analysis")
            )
        except AnalysisUnavailable:
            logger.exception("query analysis unavailable — refusing (fail closed)")

    # Fail closed: without a verdict we do not retrieve and do not generate.
    if analysis is None:
        timings.mark_first_token()
        _log_completion("unavailable", query, len(turns), timings)
        return PlainTextResponse(
            UNAVAILABLE_REPLY, headers=_headers(request_id, "unavailable")
        )

    if not analysis.safe:
        logger.warning("refused unsafe request category=%s", analysis.category)
        timings.mark_first_token()
        _log_completion("refused", query, len(turns), timings)
        return PlainTextResponse(
            REFUSAL_REPLY, headers=_headers(request_id, "refused")
        )

    return StreamingResponse(
        _stream_answer(query, turns, analysis, request_id, timings),
        media_type="text/plain",
        headers=_headers(request_id, "answered"),
    )
