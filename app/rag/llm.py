"""Generation: stream a reply from Claude, grounded in retrieved context."""
import logging

from collections.abc import AsyncIterator
from functools import lru_cache

import anthropic

from app.config import get_settings
from app.logging_config import APP_LOGGER

MAX_TOKENS = 1024

SYSTEM_PROMPT = (
    "You are a customer-support assistant. Answer the user's question using only "
    "the reference documents provided in their message. If the documents do not "
    "contain the answer, say so plainly instead of guessing."
)

ERROR_REPLY = "Sorry — I could not reach the assistant just now. Please try again."

# TODO: enable Claude's native citations once retrieval returns real chunks with
# metadata, and fall back to a canned reply when a response carries none
# (requirements.md §6.3).
# TODO: guardrails on user input — prompt-injection protection and role
# separation (requirements.md §6.3). The delimiters below are structure, not a
# guardrail.
logger = logging.getLogger(APP_LOGGER)

@lru_cache
def _client() -> anthropic.AsyncAnthropic:
    """One client per process — it owns a connection pool."""
    return anthropic.AsyncAnthropic(
        api_key=get_settings().anthropic_api_key.get_secret_value()
    )


def _build_prompt(query: str, context: list[str]) -> str:
    """Retrieved documents before the question (requirements.md §6.4)."""
    documents = "\n\n".join(context)
    return f"<reference_documents>\n{documents}\n</reference_documents>\n\n{query}"


async def stream_completion(query: str, context: list[str]) -> AsyncIterator[str]:
    """Stream a reply grounded in the given context chunks.

    No thinking and a small `max_tokens`: the 5s budget in requirements.md §7.2
    leaves little room, and `output_config.effort` errors on Haiku 4.5.
    """
    prompt = _build_prompt(query, context)
    logger.debug(f"For query '{query}', with context '{context}', final prompt '{prompt}'")
    try:
        async with _client().messages.stream(
            model=get_settings().anthropic_model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except anthropic.APIError:
        # The response has already started, so this appends to whatever streamed
        # before the failure rather than replacing it.
        yield ERROR_REPLY
