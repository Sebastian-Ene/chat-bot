import pytest

from app.rag.retriever import retrieve


@pytest.mark.anyio
async def test_retrieve_returns_non_empty_chunks() -> None:
    chunks = await retrieve("what are your support hours?")

    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) and chunk for chunk in chunks)
