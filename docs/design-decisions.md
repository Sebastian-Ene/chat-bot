# Key design decisions and trade-offs

One line of reasoning each; the long form is in `docs/considerations.md`.

## Retrieval

| Decision | Why | Trade-off |
|---|---|---|
| **Hybrid dense + sparse, RRF fused** | An error code like `F250` has to survive as a term, not be smeared into a topic vector | Two vectors per chunk |
| **One model for both vectors** (BGE-M3) | Hybrid costs one model and one forward pass, with no second lexical path to hand-roll | 2.3 GB in both images |
| **Prefetch 20, top-k 10** | RRF can only rank what the branches surfaced, so the shortlist is wider than the cut | Context tokens grow with k |
| **Original query always a branch** | A rewrite that drifts cannot retrieve worse than the raw question | One extra branch per request |
| **No re-ranking** | Out of scope for the PoC — but now warranted, not deferred | Nothing checks a chunk *answers* rather than resembles, which is what over-answering is made of |
| **No neighbour expansion** | No answer yet fails *because* a chunk was a fragment | Fragments stay possible; k=10 is the cheap mitigation |

## Ingestion

| Decision | Why | Trade-off |
|---|---|---|
| **Docling for all three formats** | One parser, one document tree, one chunker — PDF/DOCX/HTML differences stay inside it | Heavy: torch, ~8 min image builds |
| **A job, not a service** | It runs to completion in minutes and needs no network surface at all | Started by an operator or a schedule |
| **State read from the collection** | The record cannot disagree with the index | Requires a live Qdrant to plan a run |
| **Deterministic ids + one upsert** | A document is present at a hash or absent, never half-written | Shrinking documents need explicit stale deletion |
| **Describe every figure from pixels** | Chart values exist only in the image; `qa-005`/`qa-007` cannot be answered otherwise | A vision call per new figure, cached by image hash |
| **Markdown tables, not Docling triplets** | Triplets key every cell on the first column, so rows differing late read alike | None — markdown is also 28% cheaper in tokens |
| **OCR on** | Reads text rendered inside images, which the captioner transcribes unreliably | Slower parsing |

## Generation

| Decision | Why | Trade-off |
|---|---|---|
| **Claude Haiku 4.5** | Cheapest and fastest first; for grounded extraction the hard problem is retrieval | Ceiling shows in multi-hop synthesis and nuanced German |
| **Safety verdict + rewrite in one call** | Both jobs, one round trip, before retrieval | A single call to fail closed on |
| **Fails closed** | No usable verdict means refuse — never generate ungoverned | A model outage becomes a refusal |
| **Streamed** | TTFT is what the user feels, and the rewrite already spends time before it | Outcome must be settled before headers go out |
| **No citations** | Out of scope | No provenance in answers; logs keep it |
| **No prompt caching** | The only shared prefix is a ~264-token system prompt, under Haiku's 4096 floor | None |

## Backend

| Decision | Why | Trade-off |
|---|---|---|
| **Stateless history** | No store to add, and horizontal scaling stays free | The whole history is user input and must be validated and guarded |
| **Guardrails on user input only** | Indexed documents are trusted for a PoC | A poisoned corpus is undefended |
| **Caps: 10 turns / 10k chars** | Bounds cost and context per request; the client trims before sending | Long conversations lose their oldest turns |
| **Settings injected, not imported** | `common/` serves whichever child the entrypoint provides, so the ingest job carries no api credentials | One `configure()` call per entrypoint |
| **JWT in the page** | Demonstrates the mechanism end to end | **Not authentication** — anyone loading the page gets one |
| **Two log streams** | Ordinary logs at INFO, timings at DEBUG, separate files | Two files to read |

## Verification

| Decision | Why | Trade-off |
|---|---|---|
| **Golden Q&A set, LLM-judged** | Turns "high accuracy" into a number that moves when the system changes | The set is synthetic and shares the corpus's blind spots |
| **Judge on Opus 5, not Haiku** | Haiku graded three correct answers wrong, moving the score 21/21 → 18/21 with no change to the system | ~50 judge calls per run |
| **Retrieval scored on the production path** | `analyse_query()` then every branch it produces, so the figure covers what is actually served | Needs Qdrant and BGE-M3 locally |
| **Embedded Qdrant in unit tests** | Real retrieval exercised without Docker | Payload indexes are ignored there and verified against the real server |
| **Latency measured, not asserted** | Median, slowest and per-stage p95 are reported every run | No build fails on a slow answer |

## Last measured

Both golden sets, 51 questions, k=10, markdown tables, figures described.

| | |
|---|---|
| Answerable | **42/42** |
| Must decline | 5/9 — the weak axis, see Known issues #3 |
| Corpus total | 45/46 |
| Retrieval recall@10 | 41/42, MRR 0.826 |
| Latency | median 3.4 s, p95 4.97 s, slowest 5.9 s |
| Per stage (median) | analysis 1.27 s, retrieval 0.56 s, generation 1.38 s, TTFT 2.68 s |
| Tokens | median 2 747 in, 117 out |
