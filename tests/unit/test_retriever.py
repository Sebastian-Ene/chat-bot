import pytest

from app.rag.retriever import RetrievalQueries, retrieve


def test_branches_lists_only_populated_queries() -> None:
    queries = RetrievalQueries(original="support hours", rewritten="opening hours")

    assert queries.branches() == ["original", "rewritten"]


def test_branches_covers_keywords_and_sub_queries() -> None:
    queries = RetrievalQueries(
        original="a",
        rewritten="b",
        keywords=("refund", "window"),
        sub_queries=("c", "d"),
    )

    assert queries.branches() == [
        "original",
        "rewritten",
        "keywords",
        "sub_query[0]",
        "sub_query[1]",
    ]


def test_original_is_the_only_required_query() -> None:
    """A rewrite that fails or is disabled must not remove the raw query."""
    assert RetrievalQueries(original="support hours").branches() == ["original"]


@pytest.mark.anyio
async def test_retrieve_returns_non_empty_chunks() -> None:
    chunks = await retrieve(
        RetrievalQueries(original="what are your support hours?", rewritten="support hours")
    )

    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) and chunk for chunk in chunks)
