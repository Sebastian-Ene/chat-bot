import pytest

from app.rag.llm import stream_completion


@pytest.mark.anyio
async def test_stream_completion_chunks_reassemble_full_reply() -> None:
    chunks = [chunk async for chunk in stream_completion("hello", context=["some context"])]

    assert len(chunks) > 1, "expected more than one chunk — otherwise this isn't testing streaming"
    assert "".join(chunks).strip() == "This is a mocked response from the LLM."
