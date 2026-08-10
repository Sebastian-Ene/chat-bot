"""In-process stand-in for `anthropic.AsyncAnthropic`, so tests never call the API.

Mirrors only the surface `app.rag.llm` uses: `client.messages.stream(...)` as an
async context manager exposing `text_stream`.
"""
from collections.abc import AsyncIterator, Sequence
from typing import Any

STUBBED_CHUNKS = ("This ", "is ", "a ", "stubbed ", "reply.")
STUBBED_REPLY = "".join(STUBBED_CHUNKS)


async def _aiter(chunks: Sequence[str]) -> AsyncIterator[str]:
    for chunk in chunks:
        yield chunk


class _FakeStream:
    def __init__(self, chunks: Sequence[str]) -> None:
        self.text_stream = _aiter(chunks)

    async def __aenter__(self) -> "_FakeStream":
        return self

    async def __aexit__(self, *exc_info: object) -> bool:
        return False


class _FakeMessages:
    def __init__(self, chunks: Sequence[str], error: Exception | None) -> None:
        self._chunks = chunks
        self._error = error
        self.calls: list[dict[str, Any]] = []

    def stream(self, **kwargs: Any) -> _FakeStream:
        self.calls.append(kwargs)
        if self._error is not None:
            raise self._error
        return _FakeStream(self._chunks)


class FakeAnthropic:
    def __init__(
        self,
        chunks: Sequence[str] = STUBBED_CHUNKS,
        error: Exception | None = None,
    ) -> None:
        self.messages = _FakeMessages(chunks, error)
