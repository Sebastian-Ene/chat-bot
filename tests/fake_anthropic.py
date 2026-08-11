"""In-process stand-in for `anthropic.AsyncAnthropic`, so tests never call the API.

Mirrors only the surface the app uses:

- `messages.stream(...)` — async context manager exposing `text_stream` (generation)
- `messages.create(...)` — awaitable returning text content blocks (query analysis)
"""
import json
from collections.abc import AsyncIterator, Sequence
from types import SimpleNamespace
from typing import Any

STUBBED_CHUNKS = ("This ", "is ", "a ", "stubbed ", "reply.")
STUBBED_REPLY = "".join(STUBBED_CHUNKS)

STUBBED_REWRITE = "a rewritten query"
STUBBED_KEYWORDS = ["refund", "window"]
SAFE_ANALYSIS = {
    "safe": True,
    "category": "",
    "rewritten_query": STUBBED_REWRITE,
    "keywords": STUBBED_KEYWORDS,
    "sub_queries": [],
}
UNSAFE_ANALYSIS = {
    "safe": False,
    "category": "prompt_injection",
    "rewritten_query": "",
    "keywords": [],
    "sub_queries": [],
}

# Stands in for the classifier's judgement: any analysis prompt containing this
# is judged unsafe. Because the prompt carries the history too, a conversation
# that *retains* an attack turn keeps being refused — which is what makes the
# "refusal must not poison the session" behaviour testable.
UNSAFE_MARKER = "ignore all previous instructions"


async def _aiter(chunks: Sequence[str]) -> AsyncIterator[str]:
    for chunk in chunks:
        yield chunk


STUBBED_USAGE = SimpleNamespace(
    input_tokens=120,
    output_tokens=30,
    cache_read_input_tokens=0,
    cache_creation_input_tokens=0,
)


class _FakeStream:
    def __init__(self, chunks: Sequence[str]) -> None:
        self.text_stream = _aiter(chunks)

    async def __aenter__(self) -> "_FakeStream":
        return self

    async def __aexit__(self, *exc_info: object) -> bool:
        return False

    async def get_final_message(self) -> SimpleNamespace:
        return SimpleNamespace(usage=STUBBED_USAGE)


class _FakeMessages:
    def __init__(
        self,
        chunks: Sequence[str],
        error: Exception | None,
        analysis: dict | str,
        analysis_error: Exception | None,
    ) -> None:
        self._chunks = chunks
        self._error = error
        self._analysis = analysis
        self._analysis_error = analysis_error
        self.calls: list[dict[str, Any]] = []
        self.create_calls: list[dict[str, Any]] = []

    def stream(self, **kwargs: Any) -> _FakeStream:
        self.calls.append(kwargs)
        if self._error is not None:
            raise self._error
        return _FakeStream(self._chunks)

    def _payload(self, kwargs: dict[str, Any]) -> dict | str:
        if self._analysis is not None:
            return self._analysis
        prompt = kwargs["messages"][0]["content"].lower()
        return UNSAFE_ANALYSIS if UNSAFE_MARKER in prompt else SAFE_ANALYSIS

    async def create(self, **kwargs: Any) -> SimpleNamespace:
        self.create_calls.append(kwargs)
        if self._analysis_error is not None:
            raise self._analysis_error
        payload = self._payload(kwargs)
        # May be a dict (serialised for you) or a raw string, so tests can hand
        # back malformed JSON.
        text = payload if isinstance(payload, str) else json.dumps(payload)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=text)], usage=STUBBED_USAGE
        )


class FakeAnthropic:
    def __init__(
        self,
        chunks: Sequence[str] = STUBBED_CHUNKS,
        error: Exception | None = None,
        analysis: dict | str | None = None,
        analysis_error: Exception | None = None,
    ) -> None:
        # `analysis=None` means "decide from the prompt" (see `_payload`); an
        # explicit value always wins.
        self.messages = _FakeMessages(chunks, error, analysis, analysis_error)
