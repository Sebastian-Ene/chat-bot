"""The chat request flow: analyse, then retrieve and generate"""
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal

from fastapi import Response
from fastapi.responses import PlainTextResponse, StreamingResponse

from api.core.constants import (
    OUTCOME_HEADER,
    REFUSAL_REPLY,
    REQUEST_ID_HEADER,
    UNAVAILABLE_REPLY,
)
from api.core.schemas import ChatRequest
from api.core.timings import create_timings
from api.rag.llm import stream_completion
from api.rag.query_analysis import AnalysisUnavailable, analyse_query
from api.rag.retriever import RetrievalQueries, retrieve
from common.logging_config import APP_LOGGER, truncate
from common.request_context import new_request_id, set_request_id

logger = logging.getLogger(APP_LOGGER)

# `generation_failed` never reaches the client as a header — see `ChatResult`.
Outcome = Literal["answered", "refused", "unavailable"]

# Content decisions, not protocol errors, so both come back as a normal 200.
_PLAIN_REPLIES = {
    "refused": REFUSAL_REPLY,
    "unavailable": UNAVAILABLE_REPLY,
}


@dataclass(frozen=True)
class ChatResult:
    """What the flow decided, and the reply stream when there is one.

    `outcome` is what the client is told via `X-Chat-Outcome`. It is settled
    *before* streaming begins, because headers are sent before the generator is
    iterated — so a generation that fails part-way is still reported here as
    `answered`. The logs draw that distinction instead (`generation_failed`).
    """

    outcome: Outcome
    stream: AsyncIterator[str] | None = None


def _headers(request_id: str, outcome: str) -> dict[str, str]:
    # X-Request-ID ties a reply to its log lines; X-Chat-Outcome tells the client
    # whether this exchange belongs in the conversation history.
    #
    # Note `answered` is sent before the reply is generated — headers go out
    # before the stream is iterated, so a generation that fails part-way still
    # carries this header. The logs record `generation_failed` for that case.
    return {REQUEST_ID_HEADER: request_id, OUTCOME_HEADER: outcome}


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

    # Flattened to text deliberately: citations are out of scope, so the chunks
    # do not need to be document blocks. Provenance still reaches the log above.
    context = [chunk.text for chunk in chunks]

    # `stream_completion` swallows API errors and yields an apology into the
    # stream, so without this the request would be logged as answered and the
    # outage would be invisible in the logs and the timing records.
    errors: list[Exception] = []

    reply_chars = 0
    streamed = 0
    with timings.stage("generation"):
        async for chunk in stream_completion(
            query,
            context,
            history=turns,
            on_usage=timings.usage_recorder("generation"),
            on_error=errors.append,
        ):
            timings.mark_first_token()
            reply_chars += len(chunk)
            streamed += 1
            yield chunk

    logger.debug(
        "stage=generation reply_chars=%d chunks_streamed=%d", reply_chars, streamed
    )
    _log_completion(
        "generation_failed" if errors else "answered",
        query,
        len(turns),
        timings,
        chunks=len(context),
    )


async def _resolve_outcome(
    query: str, turns: list[dict[str, str]], request_id: str
) -> ChatResult:
    """Run the flow far enough to know the outcome.

    Analysis is awaited here rather than inside the generator because response
    headers are sent before the generator is iterated, so the outcome has to be
    settled first.
    """
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
        return ChatResult("unavailable")

    if not analysis.safe:
        logger.warning("refused unsafe request category=%s", analysis.category)
        timings.mark_first_token()
        _log_completion("refused", query, len(turns), timings)
        return ChatResult("refused")

    return ChatResult(
        "answered", _stream_answer(query, turns, analysis, request_id, timings)
    )


async def respond(request: ChatRequest) -> Response:
    """Handle one chat request, start to finish."""
    request_id = new_request_id()
    set_request_id(request_id)
    logger.info(
        "chat request received message_length=%d history_turns=%d",
        len(request.message),
        len(request.history),
    )

    result = await _resolve_outcome(
        request.message,
        [turn.model_dump() for turn in request.history],
        request_id,
    )
    headers = _headers(request_id, result.outcome)

    if result.stream is None:
        return PlainTextResponse(_PLAIN_REPLIES[result.outcome], headers=headers)

    return StreamingResponse(result.stream, media_type="text/plain", headers=headers)
