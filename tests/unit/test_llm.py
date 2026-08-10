import anthropic
import pytest

from app.config import get_settings
from app.rag.llm import ERROR_REPLY, MAX_TOKENS, SYSTEM_PROMPT, stream_completion
from tests.fake_anthropic import STUBBED_REPLY, FakeAnthropic


@pytest.mark.anyio
async def test_stream_completion_chunks_reassemble_full_reply(stub_anthropic: FakeAnthropic) -> None:
    chunks = [chunk async for chunk in stream_completion("hello", context=["some context"])]

    assert len(chunks) > 1, "expected more than one chunk — otherwise this isn't testing streaming"
    assert "".join(chunks) == STUBBED_REPLY


@pytest.mark.anyio
async def test_stream_completion_sends_configured_model_and_system_prompt(
    stub_anthropic: FakeAnthropic,
) -> None:
    [chunk async for chunk in stream_completion("hello", context=["some context"])]

    call = stub_anthropic.messages.calls[0]
    assert call["model"] == get_settings().anthropic_model
    assert call["system"] == SYSTEM_PROMPT
    assert call["max_tokens"] == MAX_TOKENS


@pytest.mark.anyio
async def test_stream_completion_puts_context_before_the_question(
    stub_anthropic: FakeAnthropic,
) -> None:
    """Prompt order is documents → question (requirements.md §6.4)."""
    [chunk async for chunk in stream_completion("what is the refund window?", context=["refunds take 30 days"])]

    prompt = stub_anthropic.messages.calls[0]["messages"][0]["content"]
    assert prompt.index("refunds take 30 days") < prompt.index("what is the refund window?")


@pytest.mark.anyio
async def test_stream_completion_yields_a_fallback_when_the_api_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failing = FakeAnthropic(error=anthropic.APIConnectionError(request=None))
    monkeypatch.setattr("app.rag.llm._client", lambda: failing)

    chunks = [chunk async for chunk in stream_completion("hello", context=["some context"])]

    assert "".join(chunks) == ERROR_REPLY
