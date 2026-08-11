from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetrievalQueries:
    """What retrieval searches on.

    Defined here rather than reusing `QueryAnalysis`: that model also carries the
    safety verdict, which retrieval has no business seeing. The orchestrator maps
    one to the other.

    Each populated field becomes its own `prefetch` branch, fused with RRF
    (requirements.md §6.2, §6.4). `original` always survives fusion, so a rewrite
    that drifts cannot retrieve worse than the raw query alone.
    """

    original: str
    rewritten: str = ""
    # Populated once the rewrite produces them; both are behind config flags.
    keywords: tuple[str, ...] = field(default_factory=tuple)
    sub_queries: tuple[str, ...] = field(default_factory=tuple)

    def branches(self) -> list[str]:
        """Names of the branches that will actually be searched — for the trace."""
        names = ["original"]
        if self.rewritten:
            names.append("rewritten")
        if self.keywords:
            names.append("keywords")
        names.extend(f"sub_query[{index}]" for index in range(len(self.sub_queries)))
        return names


async def retrieve(queries: RetrievalQueries) -> list[str]:
    """Mocked: return knowledge-base chunks relevant to the queries.

    Swap this out for a real vector-DB lookup (requirements.md §6.2): each
    populated field of `queries` becomes a `prefetch` branch, fused with RRF.
    """
    return ["This is a mocked retrieved document chunk."]
