# TODO

> A run-list of tasks. No rationale — decisions live in
> `docs/requirements.md`, their reasoning in `docs/considerations.md`.
> Struck-through items are done.

## Setup
- ~~Create a proper py project~~
- ~~Add a project description for AI~~

## Backend
- ~~Create b-e with Python (FastAPI)~~
- ~~Mock RAG/LLM responses so the API contract exists before real RAG is wired in~~
- ~~Chat endpoint(s) serving the mocked responses, streamed~~
- ~~Validate the chat message field (non-blank, length bounds)~~
- Extend `POST /api/chat` to accept prior turns; cap turn count and total length
- Validate and guard every turn, not just the latest
- Change `retrieve()` to return chunks with metadata, not `list[str]`
- Query rewrite step: structured output returning a query string, run before retrieval
- Retrieve on both original and rewritten query as separate `prefetch` branches, fused with RRF
- Run CPU-bound models (embedder, vision model) in a thread pool behind a bounded semaphore
- ~~Record TTFT and total completion per request, plus per-stage timers~~ (`app/timings.py`) — retrieval and generation are timed; rewrite/embed/search/expansion get timed as they are built, no collector change needed
- ~~Split logging: ordinary logs at INFO, timings at DEBUG, separate files~~ (`app/logging_config.py`)
- Produce a latency breakdown to present, not just pass/fail against 5s — raw per-request breakdown lands in `logs/performance.log`; the presentable summary comes with the eval harness
- ~~API key and secret management: `.env` → OS env, no credentials in source~~ (`app/config.py`)
- ~~Add `.env` to `.gitignore` and commit a placeholder `.env.example`~~
- Document any additional security considerations

## Frontend
- ~~Turn `app/templates/index.html` into an actual chat interface~~
- ~~JS chat widget consuming a streaming response from `/api/chat`~~
- ~~Fix accessible color contrast on chat bubbles~~
- ~~Fix chat title scrolling out of view during long conversations~~
- ~~Fix conversation log not scrolling to reveal the latest reply~~
- Send prior turns with each request

## Test document corpus
- Generate 50 initial docs: PDF/DOCX/HTML mix, 1-25 pages, ~50/50 EN/DE, ~20% cross-lingual overlap
- Make the corpus deliberately hard: multi-column pages, tables spanning page breaks, unruled tables, charts existing only as images
- Give most figures a visible caption; leave a deliberate portion with none
- Generate the golden Q&A set from the same step: table-only answers, image-only answers, cross-lingual pairs, multi-hop, and unanswerable questions
- Generate a follow-up batch of 5 docs
- Generate a further batch of 10 docs

## RAG — Read (ingestion)
- Write the module that loads and parses docs via Docling
- Image descriptions: use `PictureItem.captions` when present; generate with a vision model when absent, across all three formats
- Build caption generation as our own pipeline stage
- Record description provenance (`extracted` / `generated`) on each image
- Cache generated captions by image hash
- Ensure caption generation runs before chunking, writing captions back into the `DoclingDocument`
- Support incremental ingestion via a content-hash manifest

## RAG — Store
- Chunk with `HybridChunker` (BGE-M3 tokenizer, `max_tokens` ~512, table header repeat on overflow)
- Embed `contextualize()` output; store raw chunk text separately for display
- Set up the Qdrant collection: named dense + sparse vectors sized for BGE-M3
- Derive point IDs as `uuid5(doc_id, chunk_index)`
- Store chunk payload: `doc_id`, `chunk_index`, `parent_id`, `page_no(s)`, `heading_path`, `element_types`, `lang`, `source_format`, `caption_provenance`, `doc_content_hash`
- Implement hybrid retrieval via the Query API (`prefetch` dense + sparse, RRF fusion)
- Implement neighbour expansion: fetch siblings by payload filter on (`doc_id`, `chunk_index` range), merge overlapping windows, clamp to `parent_id`
- Use Qdrant's embedded mode (`:memory:` / local path) in unit tests

## RAG — Generate
- ~~Integrate the LLM via API, replacing the mocked responses~~ (`app/rag/llm.py`)
- ~~Keep model configuration in one place~~ (`app/config.py`)
- ~~Do not use `output_config.effort` — it errors on Haiku 4.5~~
- Assert `cache_read_input_tokens > 0` in a test — blocked: Haiku 4.5's prompt-cache
  minimum is 4096 tokens, which the current prompt is nowhere near. Revisit once
  real retrieved chunks push the prefix past it
- Enable citations on the generation call; fall back to a canned reply when a response carries none (TODO in `app/rag/llm.py`)
- Implement prompt guardrails on user input (TODO in `app/rag/llm.py`):
    - Protection against prompt injection
    - Clear system instructions and role separation
    - Constraints keeping responses aligned with the knowledge base

## Ops / Packaging
- `docker-compose.yml`: backend service + Qdrant, no load balancer
- Docker image builds via `uv`
- Bake model weights into the image at build time so first run is offline
- Verify `docker compose up` gives a working app with no manual DB setup
- Package the whole project as a single zip for delivery

## Testing
- ~~Set up Playwright (`pytest-playwright`) e2e testing with an accessible-role/text locator convention~~
- ~~e2e tests: page loads with expected elements; title/input stay pinned on long conversations; log scrolls to reveal latest reply~~
- ~~Unit tests for the mocked RAG functions and API tests for `POST /api/chat`~~
- Decide: how to demonstrate/measure answer accuracy and reliability
- Build the eval harness: retrieval metrics (recall@k, MRR) and answer correctness
- Single-prompt latency tests asserting completion under 5s
- Lightweight concurrent-users test showing no unacceptable degradation

## Deferred (only if time allows)
- Re-ranking
- Compare BGE-M3 against a smaller embedder on the golden Q&A set
- Multi-turn eval cases
- Verification spikes: `PictureItem.image` on DOCX/HTML; whether `HybridChunker` emits pictures as their own chunks

## Docs
- Architecture overview
- Key design decisions and trade-offs
- Chosen models, tools, and technologies
- ~~Track prompts used during development~~ (`scripts/export_chat_log.py`)
- ~~Note the AI trace capture is Claude-Code-only~~ (`docs/considerations.md`)
