"""Generation: stream a reply from Claude, grounded in retrieved context."""
import logging

from collections.abc import AsyncIterator, Callable

import anthropic

from app import anthropic_client
from app.config import get_settings
from app.guardrails import SYSTEM_PROMPT, guard
from app.logging_config import APP_LOGGER, truncate
from app.timings import TokenUsage

MAX_TOKENS = 1024

ERROR_REPLY = "Sorry — I could not reach the assistant just now. Please try again."

# TODO: enable Claude's native citations once retrieval returns real chunks with
# metadata, and fall back to a canned reply when a response carries none
# (requirements.md §6.3).
logger = logging.getLogger(APP_LOGGER)

def _build_prompt(query: str, context: list[str]) -> str:
    """Retrieved documents before the question (requirements.md §6.4).

    Context is not guarded: indexed documents are trusted for this PoC, and the
    guardrail scope is user input only (§6.3).
    """
    documents = "\n\n".join(context)
    return (
        f"<reference_documents>\n{documents}\n</reference_documents>\n\n"
        f"<user_message>\n{guard(query, source='question')}\n</user_message>"
    )


def _guard_history(history: list[dict[str, str]] | None) -> list[dict[str, str]]:
    """Every turn is guarded, not just the latest — including assistant turns,
    which the client supplies and can therefore forge (§6.4)."""
    return [
        {"role": turn["role"], "content": guard(turn["content"], source=f"history:{turn['role']}")}
        for turn in (history or [])
    ]


async def stream_completion(
    query: str,
    context: list[str],
    history: list[dict[str, str]] | None = None,
    on_usage: Callable[[TokenUsage], None] | None = None,
) -> AsyncIterator[str]:
    """Stream a reply grounded in the given context chunks.

    Prompt order is system → history → documents → question (requirements.md
    §6.4). The model sees prior turns but only the *current* turn's retrieved
    chunks.

    No thinking and a small `max_tokens`: the 5s budget in requirements.md §7.2
    leaves little room, and `output_config.effort` errors on Haiku 4.5.
    """
    prompt = _build_prompt(query, context)
    messages = [*_guard_history(history), {"role": "user", "content": prompt}]
    logger.debug(
        # repr keeps the whole line greppable by request id — a raw multi-line
        # prompt would leave its later lines unprefixed.
        "stage=prompt system_chars=%d prompt_chars=%d history_turns=%d prompt=%r",
        len(SYSTEM_PROMPT),
        len(prompt),
        len(messages) - 1,
        truncate(prompt),
    )
    logger.debug(messages)
    try:
        async with anthropic_client.get_client().messages.stream(
            model=get_settings().anthropic_model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text
            if on_usage is not None:
                # Only available once the stream is drained.
                final = await stream.get_final_message()
                on_usage(TokenUsage.from_sdk(getattr(final, "usage", None)))
    except anthropic.APIError:
        # The response has already started, so this appends to whatever streamed
        # before the failure rather than replacing it.
        yield ERROR_REPLY
