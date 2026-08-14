# Architecture

Reasoning lives in `docs/considerations.md`; this is the shape of the system.

## Deployment units

Two long-running services and a job, via `docker-compose`. No load balancer.

```
        browser
           │  HTTP + streamed text
           ▼
    ┌─────────────┐        ┌──────────┐
    │     api     │───────▶│  qdrant  │◀───────┐
    │  FastAPI    │ search └──────────┘ upsert │
    │  + BGE-M3   │                            │
    └─────────────┘                     ┌─────────────┐
           │ HTTPS                      │   ingest    │
           ▼                            │  job, batch │
     Anthropic API                      │  + Docling  │
           ▲                            └─────────────┘
           └──── figure descriptions ──────────┘ 
```

| Unit | Kind | Owns |
|---|---|---|
| **api** | service | frontend, query analysis, embedding, search, generation |
| **qdrant** | service | vectors + chunk payloads, on a named volume |
| **ingest** | one-shot job | Docling parsing, figure description, chunking, index-time embedding |

Ingestion is minutes of pinned CPU, so it never shares a container with the
request path. It has **no network surface**: no endpoint, no path argument
(the root is the `CORPUS_DIR` setting), corpus mounted read-only.

BGE-M3 lives in both images — index-time and query-time embeddings must come
from the same model.

## Code layout

| Package | Deployed in | Contents |
|---|---|---|
| `api/` | api image | `routers/` (paths only), `services/` (flow), `rag/` (analysis, retrieval, generation, guardrails), `core/` (config, schemas, constants, security, timings) |
| `ingestion/` | ingest image | discovery, state, parse, describe, chunk, index, runner |
| `common/` | both | config base, embedding, vector store, logging, request context |

`common/` owns no settings instance. Each entrypoint injects its own child —
`ApiSettings` or `IngestSettings` — through `configure()`, so the ingest job
needs no Anthropic key or JWT secret.

## Query pipeline

```
user message + history
  → analysis        one Haiku call: safety verdict + query rewrite (keywords, sub-queries)
  → embed           BGE-M3, one batched pass over every branch, off the event loop
  → search          Qdrant Query API: dense + sparse prefetch per branch (20), RRF fused, top 10
  → generate        Claude Haiku 4.5, streamed to the client
```

Analysis is awaited before the response starts, because the outcome must be
settled before headers are sent. Retrieval and generation then run inside the
stream.

- **Fails closed** — no usable safety verdict means refuse, without retrieving.
- **Degrades, not 500s** — unreachable Qdrant returns no chunks and the model
  says it cannot answer.
- Prompt order is system → history → documents → question.
- The model sees prior turns but only the *current* turn's chunks.

Outcomes (`answered` / `refused` / `unavailable`) return as `X-Chat-Outcome`,
paired with `X-Request-ID` that ties a reply to its log lines.

## Ingestion pipeline

```
discover → plan → parse → describe → chunk → embed → index → delete stale
```

One document end to end at a time; a failure costs that document, logged at
ERROR with the doc_id and the stage.

- **Plan** is read from the collection itself, not a side file, so the record
  cannot disagree with the index. New / changed / unchanged / deleted.
- **Describe** runs before chunking — a figure's description is folded into the
  chunk text. Cached by image hash, so re-runs cost nothing.
- **Index** writes all of a document's points in one `wait=True` upsert at
  `uuid5(doc_id, chunk_index)`, then deletes what is stale by content hash or
  chunk count.

20 documents → **201 chunks**. Parsing dominates the runtime.

## State

Nothing is stored server-side except vectors. Conversation history arrives from
the client on every request, capped at 10 turns / 10 000 chars / 4 000 per turn,
and every turn is validated and guarded — assistant turns included, since a
caller can forge them.

## Chunk payload

`doc_id`, `chunk_index`, `parent_id`, `page_numbers`, `headings`,
`source_format`, `doc_content_hash`, and the chunk `text` — so retrieval answers
in one round trip and the api never mounts the corpus.
