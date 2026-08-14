"""Routing only: paths and methods onto the code that handles them, plus the
dependencies each route needs. Anything a request *does* belongs in a service.
"""
from fastapi import APIRouter, Depends, Response
from fastapi.responses import PlainTextResponse

from api.core.constants import OUTCOME_HEADER, REQUEST_ID_HEADER
from api.core.schemas import ChatRequest
from api.core.security import verify_token
from api.services.chat import respond

router = APIRouter(prefix="/api")

# The reply is a stream of plain text, and the two headers are the only way a
# client learns what happened — neither is inferable from the return type, so
# both are spelled out here. 422 is left to FastAPI, which documents it from
# `ChatRequest`.
_CHAT_RESPONSES = {
    200: {
        "description": (
            "The reply, streamed as plain text. A refusal and an unavailable "
            "service also arrive as 200 — they are content decisions, not "
            "protocol errors. Read the outcome header to tell them apart."
        ),
        "content": {"text/plain": {"schema": {"type": "string"}}},
        "headers": {
            OUTCOME_HEADER: {
                "description": (
                    "`answered`, `refused` or `unavailable`. Only an `answered` "
                    "exchange belongs in the history sent back on the next "
                    "request. Sent before the stream is iterated, so a "
                    "generation that fails part-way still reads `answered`."
                ),
                "schema": {
                    "type": "string",
                    "enum": ["answered", "refused", "unavailable"],
                },
            },
            REQUEST_ID_HEADER: {
                "description": "Ties this reply to its server log lines.",
                "schema": {"type": "string"},
            },
        },
    },
    401: {"description": "Missing, malformed or expired page token."},
}


@router.post(
    "/chat",
    dependencies=[Depends(verify_token)],
    summary="Ask a question about the corpus",
    response_class=PlainTextResponse,
    responses=_CHAT_RESPONSES,
)
async def chat(request: ChatRequest) -> Response:
    return await respond(request)
