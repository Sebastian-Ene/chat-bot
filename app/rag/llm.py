from collections.abc import AsyncIterator


async def stream_completion(query: str, context: list[str]) -> AsyncIterator[str]:
    """Mocked: stream a reply grounded in the given context chunks.

    Swap this out for a real LLM API call (requirements.md §5.3).
    """
    reply = "This is a mocked response from the LLM."
    for word in reply.split(" "):
        yield word + " "
