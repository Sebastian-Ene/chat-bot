async def retrieve(query: str) -> list[str]:
    """Mocked: return knowledge-base chunks relevant to the query.

    Swap this out for a real vector-DB lookup (requirements.md §5.2).
    """
    return ["This is a mocked retrieved document chunk."]
