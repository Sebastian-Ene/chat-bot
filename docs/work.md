# TODO

> A run-list of tasks. No rationale — decisions live in
> `docs/requirements.md`, their reasoning in `docs/considerations.md`.
>
> Within each section, outstanding work comes first. Everything below the
> `--- Done ---` delimiter is finished (and struck through).

## Setup

--- Done ---
- ~~Create a proper py project~~
- ~~Add a project description for AI~~

## Backend

--- Done ---
- ~~Bound the query embedder with a semaphore~~ — **won't do**: embedding is ~1% of a request, the shared thread pool already caps it at 40, and rate limits bind far sooner
- ~~Document any additional security considerations~~ — `docs/considerations.md` → Security: secrets via `.env`, ingestion's absent inbound surface (no path argument, read-only corpus) and its new *outbound* egress since figure description, and why the page token is a demonstration rather than authentication
- ~~Produce a latency breakdown to present, not just pass/fail against 5s~~ — `scripts/eval_golden.py` joins each answer to the api's own per-stage timings on `X-Request-ID` and reports median/p95/max per stage, in the console and the Markdown report. Answered requests only: a refusal never reaches retrieval or generation. Degrades to nothing when the log is absent (DEBUG-only, and a remote `--base-url` has no local log)
- ~~Create b-e with Python (FastAPI)~~
- ~~Mock RAG/LLM responses so the API contract exists before real RAG is wired in~~
- ~~Chat endpoint(s) serving the mocked responses, streamed~~
- ~~Validate the chat message field (non-blank, length bounds)~~
- ~~Extend `POST /api/chat` to accept prior turns; cap turn count and total length~~ (10 turns, 10 000 chars total, 4 000 per turn)
- ~~Record TTFT and total completion per request, plus per-stage timers~~ (`api/core/timings.py`) — retrieval and generation are timed; rewrite/embed/search/expansion get timed as they are built, no collector change needed
- ~~Split logging: ordinary logs at INFO, timings at DEBUG, separate files~~ (`common/logging_config.py`)
- ~~API key and secret management: `.env` → OS env, no credentials in source~~ (`common/config.py`)
- ~~Add `.env` to `.gitignore` and commit a placeholder `.env.example`~~
- ~~API endpoint security: JWT embedded in the chat page, sent with every request, signature + TTL checked~~ (`api/core/security.py`) — opt-in per endpoint via `dependencies=[Depends(verify_token)]`; documented as a demonstration, not auth
- ~~Validate and guard every turn, not just the latest~~ — validation in `api/core/schemas.py` (shape, bounds, caps, leading-user rule), guarding in `api/rag/guardrails.py` (question and every history turn, assistant turns included)
- ~~Query rewrite step: structured output returning a query string, run before retrieval~~ (`api/rag/query_analysis.py`) — merged with an LLM safety verdict into one call; fails closed
- ~~Validate history against tampering~~ — the analysis call judges the whole conversation, not just the latest message, and refuses with `forged_history` when a prior assistant turn reads as fabricated. This is judgment, not integrity: a subtly-worded forgery can still pass, and that is accepted
- ~~`retrieve()` returns chunks with metadata, not `list[str]`~~ — `RetrievedChunk` carries doc_id, pages, headings and `parent_id`
- ~~Retrieve on original and rewritten query as separate `prefetch` branches, fused with RRF~~ — `RetrievalQueries` carries every branch; the mock is gone
- ~~`GET /health` for the container probe~~ (`api/routers/health.py`) — unauthenticated; the HEALTHCHECK previously hit `/`, rendering the template and minting a JWT every 15s
- ~~A failed generation is no longer logged as `answered`~~ — `stream_completion` reports the error via `on_error` and the flow logs `generation_failed`. The `X-Chat-Outcome` header still says `answered`: it is sent before the stream is iterated
- ~~Query embedder off the event loop~~ — `anyio.to_thread`, one batched forward pass for all branches
- ~~Load the embedder at api startup~~ — the first request otherwise paid 4 s of model load inside its own latency budget (12.7 s cold vs 3.6–5.0 s warm)

## Frontend

--- Done ---
- ~~Grow the input as the message gets long~~ — a `<textarea>` that auto-grows to ~5 lines then scrolls, so a pasted wall of text cannot squeeze the conversation off screen. Enter sends and Shift+Enter writes a newline, since a textarea's default would leave a chat box that needs the mouse to send
- ~~Turn `api/templates/index.html` into an actual chat interface~~
- ~~JS chat widget consuming a streaming response from `/api/chat`~~
- ~~Fix accessible color contrast on chat bubbles~~
- ~~Fix chat title scrolling out of view during long conversations~~
- ~~Fix conversation log not scrolling to reveal the latest reply~~
- ~~Send prior turns with each request~~ (trims to the server's caps so long conversations don't start 422ing)

## Test document corpus
- A/B `REWRITE_KEYWORDS_ENABLED` and `REWRITE_SUB_QUERIES_ENABLED` on the golden Q&A set — both branches are reasoned, not measured, and may be noise. Unblocked now the harness exists: flip each flag and re-run

--- Done ---
- ~~Pilot batch of 5 docs~~ (`corpus/`, generated by `scripts/generate_corpus.py`) — every deliberately-hard aspect covered at least once; see `docs/corpus.md` for the coverage matrix
- ~~Make the corpus deliberately hard: multi-column pages, tables spanning page breaks, unruled tables, charts existing only as images~~ — all four present and visually verified in batch 1
- ~~Give most figures a visible caption; leave a deliberate portion with none~~ — both paths exercised (see the caption-skew item above)
- ~~Generate the golden Q&A set from the same step~~ (`corpus/golden_qa.json`) — 26 questions (21 initial + 5 later) across table-only, near-miss, image-only, prose, unanswerable, cross-lingual and multi-hop
- ~~Build the content-as-data renderer~~ (`markdown_kit` + `renderers`) — Markdown under `scripts/corpus/content/`, three layout variants
- ~~Generate 15 distractor docs to reach 20 initial~~ — near-miss content on purpose; 10 EN, 9 DE, 1 mixed across the initial 20
- ~~Include at least one document near the 25-page bound~~ — `fehlercode-referenz-de.pdf` is 25 pages, ~350 codes, generated combinatorially
- ~~Skew toward captioned figures~~ — 4 of 6 figures captioned
- ~~Extend the golden Q&A set to cover the distractors~~ — 4 near-miss questions plus one deep inside the 25-page reference
- ~~Add a corpus consistency check~~ (`scripts/check_corpus.py`) — catches golden answers naming documents or values that don't exist, and batch/document mismatches
- ~~Generate the later batch of 5 docs~~ (`corpus/docs-later/`) — new topics, no contradictions; 5 `batch: later` golden questions must be declined before ingestion and answered after

## RAG — Read (ingestion)

--- Done ---
- ~~Image descriptions~~ (`ingestion/describe.py`) — Claude vision via Docling's `PictureDescriptionApiOptions` + `api_image_request`, pointed at Anthropic's OpenAI-compatible endpoint; written to `PictureItem.meta` before chunking, cached by image hash so re-ingestion and `--force` cost nothing. Took `qa-005` and `qa-007` from declining to correct. Docling's *own* enrichment is PDF-only, which is why the request is driven by us: HTML figures carry no image bytes and are loaded from `<img src>` relative to the document
- ~~Prompt for transcription, not captioning~~ — "list every series and its value at each labelled position". A generic caption cannot answer `qa-005`, whose value exists only as a plotted point. Haiku transcribed the −10 °C series exactly; the neighbouring series drifted 1–3 points and one annotation was attributed to the wrong curve, so treat descriptions as searchable text rather than a data source
- ~~Extend the run summary with picture counts and descriptions generated vs cached~~ — `described=` and `cached=` on the per-document line
- ~~Unit test the caption cache — fixtures only, no models~~ (`tests/ingest/test_describe.py`) — cache round-trip, corrupt-file tolerance, content-addressed hashing, and HTML `<img src>` resolution
- ~~Recursive walk for `.pdf`/`.docx`/`.html` at any depth, stable ordering~~ (`ingestion/discovery.py`) — skips dotfiles and the golden answer key
- ~~`doc_id` = path relative to the corpus root; `doc_content_hash` = SHA-256 of file bytes~~
- ~~Work out what a run has to do~~ (`ingestion/state.py`) — read from the collection rather than a side file, so the record cannot disagree with the index; new/changed/unchanged/deleted, with a multi-hash document treated as a partial write and re-ingested
- ~~Act on the plan~~ — index `new` + `changed`, skip `unchanged`, delete the vectors of `deleted`; all four verified end to end against the running stack
- ~~Write all of a document's points in a **single upsert**~~ — atomically indexed at a hash or not at all; `state.py` reads that invariant back
- ~~One Docling `DocumentConverter`, OCR on, table structure on, per-format options~~ (`ingestion/parse.py`) — built once per process; `generate_picture_images` on, or figure images are discarded and the caption stage has nothing to work with
- ~~Wrap in a `ParsedDocument`~~ — `doc_id`, source format, content hash, page/table/picture counts and parse duration
- ~~A document that fails to convert is logged at ERROR and skipped~~ — one malformed file must not block the corpus; it stays un-indexed and is retried next run. **Production would alert on these ERROR lines** so a document that never parses cannot fail silently
- ~~No `lang` field~~ — nothing supplies it for free and BGE-M3 is multilingual, so retrieval does not need it
- ~~`TORCHDYNAMO_DISABLE=1` before torch is imported~~ — set in every module that reaches torch; without a C compiler in the image, every conversion fails otherwise
- ~~`page_no` only ever populates for PDF~~ — DOCX and HTML chunks carry an empty page list, and citations must tolerate that rather than treat it as an error
- ~~A page-spanning table arrives as **two** table objects~~ — accepted, not worked around: each half chunks as a complete-looking table with its header repeated
- ~~Ingestion is a **job, not a service**~~ — it runs to completion, is started by an operator or a schedule, and takes minutes; that is a batch job, and it needs no network surface at all
- ~~`run()` ties the pipeline together~~ (`ingestion/runner.py`) — discover → plan → parse → chunk → embed → index, one document at a time, returning a `RunReport`
- ~~`python -m ingestion` over the `CORPUS_DIR` setting~~ (`ingestion/__main__.py`) — `--force` re-processes everything, `--dry-run` prints the plan and stops. No directory argument: the root is a setting, so a run cannot be aimed at arbitrary host files
- ~~Exit non-zero when a document failed~~ — a scheduled run must not report success over a partially indexed corpus
- ~~The ingest container is a one-shot job~~ — `docker compose run --rm ingest`, behind an `ingest` profile so `docker compose up` does not start it; no port, no healthcheck, no server
- ~~Integration tests over real corpus files~~ — `tests/ingest/test_parse_documents.py` and `test_chunk_documents.py`, behind the `docling` marker and out of the default run
- ~~Spike: does `PictureItem.image` yield image bytes for DOCX and HTML?~~ (`scripts/spikes/docling_pictures.py`) — PDF yes, DOCX yes, **HTML no**; DOCX captions are never associated, and a PDF caption can be OCR'd in-image text
- ~~Spike: how does a picture reach the chunker?~~ (`scripts/spikes/docling_chunking.py`) — pictures do become chunks (merged with surrounding prose), `contextualize()` prepends the heading path, and a description on `PictureItem.meta` reaches the chunk text
- ~~Add a DOCX figure to the corpus~~ — no DOCX carried an image, so the format's description path was untestable; `accessory-catalogue-en.docx` now has a captioned figure and `troubleshooting-zeitplan-de.docx` an uncaptioned one

## RAG — Store
- Watch the refusal rate across runs — Known issues #11

--- Done ---
- ~~Re-run both golden sets~~ — k=10 and markdown tables verified end to end: **answerable 42/42** (both previously-failing `conditional` questions now correct), corpus 45/46, recall@10 41/42, MRR 0.826, latency p95 4.97 s. `qa-001` no longer reads the neighbouring row
- ~~The eval harness outlived its page token~~ — one token was minted per run and `JWT_TTL_SECONDS` is 1800, so a full two-set run 401'd at question 42 of 51 and lost every result, reports included. `PageToken` now re-mints and retries once on a 401
- ~~`delete_stale` judges staleness on the chunk count too~~ — it filtered on the content hash alone, so re-chunking a byte-identical file stranded the tail: the markdown table change cost 7 orphan points across three documents, cleaned up by hand. Now `doc_id` AND (hash differs OR `chunk_index >= chunk_count`). `must` + `should` verified against the real server, not just embedded Qdrant
- ~~`retrieval_top_k` 5 → 10~~ — prefetch was already 20, so the candidates existed and only the cut changed. `qb-014` and `qb-015` each need three documents and the top 5 held duplicates, dropping a branch. Cheaper than neighbour expansion for the same effect
- ~~Tables serialised as markdown, not triplets~~ (`ingestion/chunk.py`) — Docling's default writes one `<row key>, <column> = <value>` clause per cell into a run-on paragraph keyed on the first column, so rows differing only in a later column sit adjacent and indistinguishable — the qa-001 failure. Markdown keeps one row per line under named columns and is *cheaper*: 325 tokens against 454 on the returns table. `MarkdownTableSerializer` also implements `get_header_and_body_lines`, so an oversized table still splits row-wise with its header repeated. Corpus re-ingested: 208 → 201 chunks
- ~~Use Qdrant's embedded mode in unit tests~~ — `:memory:` throughout the collection, index and retriever tests, so real retrieval is exercised without Docker. Payload indexes are the one thing it ignores, so that assertion checks the call and was verified against the real server
- ~~Chunk with `HybridChunker`~~ (`ingestion/chunk.py`) — BGE-M3's own tokenizer at `max_tokens=512`, table header repeated on overflow, peers merged. The tokenizer must be the embedder's: a chunk sized in someone else's tokens overflows silently at embed time
- ~~Embed `contextualize()` output, keep the raw text separately~~ — `embed_text` carries the heading path so a chunk is findable by its section; `text` is what reaches the LLM and the citation, since heading breadcrumbs in the prompt end up in the answer
- ~~Corpus baseline~~ — 20 documents → **207 chunks** in 3.6 s (pdf 132, docx 40, html 35); median 90 tokens, mean 175, max 519. Chunking is negligible next to the 180 s parse
- ~~The budget applies to the raw chunk, not `embed_text`~~ — Docling sizes the chunk then prepends the heading path, so 27 of 207 run up to 7 tokens over. Harmless (BGE-M3 takes 8192) but downstream code must not assume 512
- ~~Embed with BGE-M3, dense + sparse~~ (`common/embedding.py`) — both from one forward pass, so hybrid costs one model. Sparse is BGE-M3's own learned lexical weights, not BM25. Shared by the job and the api: a query embedded differently from its chunks silently fails to retrieve them
- ~~`FlagEmbedding` truncates at 512 by default~~ — `embed_max_tokens=1024` set explicitly, or the 27 over-budget chunks lose their tails with nothing in any log. A test asserts the setting stays above the chunk budget
- ~~Embedding baseline~~ — 207 chunks in **13.7 s** (66 ms each), sparse terms median 52; **query embedding 33 ms**, negligible against the 5 s budget. Full ingestion is now ~194 s, still 93% parsing
- ~~Cross-lingual retrieval verified~~ — English *and* German queries both land closer to the German chunk than to an unrelated English one, which is what justified dropping translation from the rewrite step
- ~~Qdrant collection with named dense + sparse vectors~~ (`common/vector_store.py`) — both on one point, so a hybrid query prefetches each branch and fuses server-side; `doc_id` payload-indexed since every state read and delete filters on it. Verified against the real server, not just in-memory
- ~~Created by the ingest job, never the api~~ — an api that auto-creates an empty collection turns "never ingested" into "every question unanswerable"
- ~~Dense distance is **dot**, not cosine~~ — identical while embeddings are unit-norm, and skips Qdrant's normalisation pass. It goes silently wrong if normalisation is ever turned off, so the embedding tests assert unit norm and `common/vector_store.py` carries the warning
- ~~Refuse a collection built for a different embedding~~ — wrong width, wrong distance or a missing dense vector raises `CollectionMismatch` naming the fix, instead of mixing incompatible vectors and degrading retrieval quietly
- ~~Index chunks as points~~ (`ingestion/index.py`) — `uuid5(doc_id, chunk_index)` ids so re-ingesting overwrites in place; payload carries the chunk text, so retrieval answers in one round trip and the api never needs the corpus mounted. `embed_text` is not stored — it exists only to be vectorised
- ~~One upsert per document, `wait=True`~~ — the invariant `state.py` reads back: a document is present at a hash or absent, never half-written
- ~~Replace a changed document new-points-first~~ — then delete points whose hash differs. A crash between the two leaves visible duplicates repaired next run; the reverse order would make the document vanish from retrieval. Also handles a new version with *fewer* chunks, which deterministic ids alone would leave stranded
- ~~Documents deleted from disk have their points removed~~ — by `doc_id` filter, after the per-document loop
- ~~Hybrid retrieval via the Query API~~ (`api/rag/retriever.py`) — every populated branch searched on **both** vector kinds, fused server-side with RRF in one request; `retrieve()` returns `RetrievedChunk` with provenance, not strings. Prefetch (20) is wider than top_k (5): RRF can only rank what the branches surfaced
- ~~Retrieval failure degrades, not 500s~~ — an unreachable Qdrant or missing collection logs ERROR and returns nothing; the generator then says it cannot answer
- ~~Query embedding off the event loop~~ — one batched forward pass for every branch, via `anyio.to_thread`
- ~~BGE-M3 in the api image~~ — `FlagEmbedding` moved to the main dependencies and the weights baked in; the api is no longer thin (507 MB → ~7 GB) because one model emits both vector kinds and must exist wherever a vector is produced. Docling stays out, now guarded by a test rather than by hand
- ~~`parent_id` in the payload~~ — heading path scoped by `doc_id`, so neighbour expansion can clamp to a section and fifteen documents' "Introduction" do not collapse into one
- ~~Golden-set recall measured~~ — **18/18 at k=5** on the initial batch: table_only 5/5, near_miss 4/4, image_only 3/3, cross_lingual 2/2, multi_hop 2/2, prose 2/2. Retrieval latency median 55 ms. Note this is *document-level* recall, not answer correctness — the image questions find the right document, but nothing yet describes the figures. Reproduced by `scripts/eval_golden.py --retrieval` under **strict multi-hop** (a hit needs every document the question names, not just one) and `also_in` counted as an alternative source. `qa-011` sits on the k=5 boundary and flips between hit and miss across runs, so 17/18 and 18/18 are both expected outcomes — the rewrite is non-deterministic and reorders the fusion
- ~~Process each document end to end~~ (`runner.ingest_document`) — parse → chunk → embed → index, one document at a time. `parse_all`/`chunk_all` removed: holding every parsed document and embedding in memory grows with the corpus for no benefit. A failure at any stage costs one document, and the ERROR names the doc_id *and* the stage, so it can be marked for retry or editing

## RAG — Generate

--- Done ---
- ~~Assert `cache_read_input_tokens > 0` in a test~~ — **won't do**: the only prefix shared between requests is the ~264-token system prompt, far under Haiku's 4096 minimum, and no `cache_control` is set. Nothing planned changes that — documents and question are per-request
- ~~Enable citations on the generation call~~ — **won't do**, out of scope. Answers carry no provenance; the system prompt tells the model not to mention the reference documents. `RetrievedChunk.citation()` remains, used for logs only
- ~~Implement prompt guardrails on user input~~ (`api/rag/guardrails.py`):
    - ~~Protection against prompt injection~~ — sanitising always applied; detection logged, never blocking
    - ~~Clear system instructions and role separation~~
    - ~~Constraints keeping responses aligned with the knowledge base~~
    - ~~Cover every history turn, not just the current question~~
- ~~Integrate the LLM via API, replacing the mocked responses~~ (`api/rag/llm.py`)
- ~~Keep model configuration in one place~~ (`common/config.py`) — split per deployment unit: `Settings` holds what both sides read, `ApiSettings` and `IngestSettings` add their own. `common/` owns no instance; each entrypoint injects its child via `configure()`. The ingest job no longer needs an Anthropic key or JWT secret, so neither Dockerfile carries placeholder credentials
- ~~Do not use `output_config.effort` — it errors on Haiku 4.5~~
- ~~Stop the classifier inventing refusal categories~~ — it refused a benign shipping question as `category=unclear_scope`; the prompt now names the four as a closed set and marks unclear or undocumented questions safe

## Ops / Packaging
- Package the whole project as a single zip for delivery

--- Done ---
- ~~Revisit the Docker approach as a whole~~ — **won't do**, accepted as Known issues #4: the setup is development-shaped by choice. The open points stand as the rework list — nothing asserts the baked models are present, both images build in ~8 min, and the api carries BGE-M3 only because there is no embedder service
- ~~Split the dev-only bits (source mount, `--reload`) into an environment overlay~~ — **won't do** while there is one environment; same acceptance as above. `--reload` also makes the api load BGE-M3 twice
- ~~Connect to Qdrant at api startup and fail fast if unreachable~~ (`common/vector_store.py`) — verified in the container: `qdrant connected url=http://qdrant:6333`
- ~~Add the **ingest** image~~ (`Dockerfile.ingester`) — docling and torch present there and absent from the api, `/corpus` mounted read-only with all 20 documents visible
- ~~`docker-compose.yml` with qdrant, no load balancer~~ — api + qdrant up and healthy, qdrant storage on a named volume
- ~~Docker image builds via `uv`~~ (`Dockerfile.api`) — multi-stage, non-root, venv outside `/app` so the dev bind mount cannot shadow it
- ~~Keep Docling out of the api image~~ — it stays in the `ingest` dependency group; verified absent from the built image and guarded by `tests/api/test_image_boundary.py`. The api is 16.4 GB regardless, because BGE-M3 and torch's CUDA wheels live there
- ~~Mount the working tree in dev so logs land on the host~~ — `./api`, `./common`, `./ingestion` and `./logs` bind-mounted, `--reload` enabled
- ~~Model weights baked into both images~~ — immutable, no runtime download, read-only at runtime, no cache volume anywhere. The api additionally loads BGE-M3 at startup so the first question does not pay for it
- ~~Verify `docker compose up` gives a working app with no manual DB setup~~ — re-verified with real retrieval: a German question about error code F250 returned the right answer from `fehlercode-referenz-de.pdf` with page numbers, correlated to the container by request id

## Testing

--- Done ---
- ~~Lightweight concurrent-users test showing no unacceptable degradation~~ — **won't do**: single-request latency is measured and within budget, and concurrency is bounded by the Anthropic rate limit rather than by anything in this codebase
- ~~Warm the embedder before the retrieval pass~~ — `measure_retrieval` loads BGE-M3 up front (~8 s) instead of inside the first `retrieve()`, which charged `qa-001` 5.9 s against a 0.18 s median and made the per-question table a lie. The api already warmed at startup; the harness runs in its own process
- ~~Single-prompt latency tests asserting completion under 5s~~ — **won't do**: the harness already reports median and slowest per run, plus per-stage median/p95/max. Good enough; an assertion would only pick a threshold to argue about
- ~~Decide: how to demonstrate/measure answer accuracy~~ — the golden set graded by an LLM judge, scored as two figures: the ingested corpus, and the not-yet-ingested batch that must be declined
- ~~Build the eval harness~~ (`scripts/eval_golden.py`) — 26 questions against a running api, non-zero exit on any failure. **21/21** on the corpus and **3/5** declining the later batch, with recall@5 **18/18** and MRR **0.931**; findings in `docs/considerations.md` → Improvements. Answer latency median 2.9 s, slowest 5.3 s. The `3/5` is correct behaviour, not a gap: `qa-101` and `qa-105` answer from documents that are in the ingested corpus, and become expected-answer questions once `docs-later` is ingested
- ~~Judge on `claude-opus-5`, not the app's Haiku~~ — Haiku graded three correct answers wrong in one run (accurate extra detail, and a well-formed decline — both allowed by the rubrics), moving the score 21/21 → 18/21 with no change to the system under test. 26 calls per eval, so cost is not a reason to downgrade it
- ~~Add retrieval metrics to the harness~~ — `--retrieval` scores recall@k and MRR over the production path (`analyse_query()` then every branch it produces), so the figure covers the retriever as actually served. Separate opt-in pass: answer correctness needs only HTTP, this needs Qdrant and loads BGE-M3 locally
- ~~Reports land in `logs/common/`~~ — `golden_qa.json` for machines, `golden_qa.md` for people: scores, per-question tables, and a detail block per question merging both passes, so a failure reads without cross-referencing. Both gitignored as run output
- ~~Set up Playwright (`pytest-playwright`) e2e testing with an accessible-role/text locator convention~~
- ~~e2e tests: page loads with expected elements; title/input stay pinned on long conversations; log scrolls to reveal latest reply; conversation keeps succeeding past the history cap~~
- ~~Unit tests for the mocked RAG functions and API tests for `POST /api/chat`~~

## Deferred (only if time allows)

--- Done ---
- ~~Neighbour expansion~~ — **won't do**, Known issues #7: it needs an answer that is wrong *because a chunk was a fragment*, and `retrieval_top_k` 10 covers the cheap end of that. When it lands, `point_id()` has to leave `ingestion/index.py` first — that module imports docling, which must not reach the api
- ~~Rate limiting on `/api/chat`~~ — **won't do**, Known issues #8: the real fix is user authentication and a per-user limit, not a limiter on a public endpoint
- ~~Tooling: ruff, mypy, pre-commit, CI, coverage, dependency pinning audit~~ — **won't do**, Known issues #9: consistency and collaboration rather than working software. The `# noqa: E402` comments on the deliberately-late imports are already written but inert until a linter exists
- ~~Re-ranking~~ — **won't do here**, but no longer for want of evidence: over-answering (Known issues #10) is the trigger, and #3 carries the full argument — five relevant chunks beat ten with misses, cost moves to re-rank compute, which argues for splitting model inference into its own service and reclaiming latency from the query-rewrite call. Out of scope for a timed PoC, not unjustified
- ~~Multi-turn eval cases~~ — **won't do**, Known issues #6: needs an agentic harness and tool development, and the corpus is not large enough to invite questions that reference earlier answers
- ~~Add a SQL DB to store sessions~~ — **won't do**, Known issues #5. Accepted consequence: no server-side sessions, and no usage data to analyse
- ~~Conflict/recency test in the corpus~~ — **won't do**, Known issues #1: the corpus is synthetic, and adding contradictions to it tests the generator against invented conflicts rather than real ones
- ~~Add 10 more large files > 15 pages to the corpus~~ — **won't do**, Known issues #1/#2: more synthetic documents grow the set without addressing what makes it weak

## Docs

--- Done ---
- ~~Try swagger or another way of docing the API~~ — FastAPI already serves `/docs`, `/redoc` and `/openapi.json`. Made them usable: the page token is a declared `HTTPBearer` scheme so `/docs` has an Authorize button, and `/api/chat` documents its 401, its `text/plain` stream and both response headers. UI assets load from a CDN — not self-hosted, so `/docs` needs internet
- ~~Architecture overview~~ (`docs/architecture.md`) — deployment units, code layout, both pipelines, state
- ~~Key design decisions and trade-offs~~ (`docs/design-decisions.md`) — one line each, grouped by area, with the trade-off named
- ~~Chosen models, tools, and technologies~~ (`docs/technologies.md`) — models, runtime versions, tooling, commands
- ~~Track prompts used during development~~ (`scripts/export_chat_log.py`)
- ~~Note the AI trace capture is Claude-Code-only~~ (`docs/considerations.md`)
