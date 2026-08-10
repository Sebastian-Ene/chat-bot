# Considerations

> **What this document is.** The development narrative — the decisions taken,
> why they were taken, what was rejected and what trade-offs were accepted. This
> is the document intended for presentation.
>
> It is the *why* behind `docs/requirements.md`, which records the *what*.
> Section references point back to it. Tasks live in `docs/work.md`.

A recurring policy runs through most of these decisions: **take the cheapest
option that could work, and upgrade only on measured evidence.** It applies to
the embedding model, the image captioner and the LLM. The cost of that policy is
that it requires an evaluation harness to be actionable — which is why the
accuracy question is the last open one and has the most riding on it.

## Scope

Just a POC.

Not having any initial data makes it harder to ensure the solution addresses
all cases.

## Architecture

Use uvicorn + fastapi for speed (async).

Original sketch:

    Nginx/AWS load balancer ->((server docker): uvicorn -> fastapi app )-> ( (db docker) vector db)

**Superseded:** the Nginx/load-balancer tier was dropped as unnecessary for a
PoC. The shipped shape is two containers via `docker-compose` — backend
(uvicorn + FastAPI, also serving the frontend) and the vector DB — with no LB
in front. Priority is a smooth install for another dev: `docker compose up`
should bring up the app with the vector DB already configured (requirements §5).

## Document corpus

### Generating the corpus — the self-set-exam trap

We author both the corpus and the pipeline that reads it. The obvious failure
mode is generating documents that happen to be easy for our own parser, which
makes the pipeline look good and proves nothing. The brief explicitly asks for
"mixed layouts" and "embedded information that requires careful processing", so
the corpus has to be *deliberately* hard — multi-column pages, unruled tables,
tables spanning page breaks, charts that exist only as images, and a portion of
figures with no visible caption so the generated-caption path actually fires.
The full specification is in requirements §4.

The same principle applies to the golden Q&A set: questions whose answers live
only in a table or only in a chart image are the ones that prove the pipeline
works.

## Document parsing

### Docling, unified across all three formats

Alternatives considered: best-of-breed per format (pdfplumber + python-docx +
BeautifulSoup), other unified parsers (Unstructured, Marker, MinerU), cloud
document-AI (LlamaParse, Azure Document Intelligence, Textract), and
LLM-as-parser (render pages to images, send to Claude vision).

- **Cloud document-AI — rejected.** Conflicts with the local/reproducible
  posture and adds another vendor and API key.
- **Per-format libraries — rejected.** Genuinely defensible: DOCX and HTML
  already carry table structure natively, so ML parsing buys nothing there, and
  PDF is the only hard format. But it means three parsers, three sets of edge
  cases and three things to explain, all behind a hand-written common
  interface. Also worth noting on licensing: PyMuPDF, the fastest PDF option,
  is AGPL — awkward for a submission. pdfplumber (MIT) would have been the
  pick.
- **Docling — chosen.** One library and one output model for all three formats.
  Critically, it emits a **structured document tree** (headings, paragraphs,
  tables, images, with page and section provenance) rather than a flat Markdown
  string — that provenance is what makes table-aware chunking and page-level
  citations possible. Layout analysis plus dedicated table-structure
  recognition covers the PDF case. MIT licensed.
- **Trade-off accepted:** ships ML models, so a bigger image and slower ingest.
  Ingest is offline, so it never touches the 5s completion target.

Docling's `HybridChunker` also turned out to settle most of the chunking
decision — see below.

### OCR — kept on

The corpus is digital-native, so OCR isn't needed for page text and switching it
off would be a free speedup. Kept on anyway because OCR reads text rendered
*inside* images — chart axis labels, legends, numbers baked into diagrams —
which the captioner does not reliably transcribe. The two complement each other
on exactly the figures that matter.

### Images — caption-first, generate only the gaps

Goal: every image ends up with an indexed, referenceable text description. Use
the caption the document already carries; only generate one when there isn't
one. The source of an existing description is **`PictureItem.captions`** — the
visible "Figure N: …" text Docling's layout analysis associates with the figure.
This works across all three formats and needs no extra code.

**Accessibility metadata is deliberately out of scope.** An earlier version of
this design was alt-text-first: prefer HTML `alt` / DOCX `descr` / PDF `/Alt`,
generate only when absent. Research into Docling killed it:

- Docling's HTML backend never reads the `alt` attribute (it handles `href`,
  `hidden`, `aria-hidden`, `style`, `id`, `class`, `start` — not `alt`), and its
  DOCX backend never reads `docPr`/`descr`.
- `PictureItem` has no field to hold such a value anyway. Its fields are
  `label`, `annotations`, `image`, `prov`, plus `captions` / `references` /
  `footnotes` inherited from `FloatingItem`. Only `captions` and VLM
  `annotations` carry text.

Getting alt text would therefore mean parsing each source file a second time
and joining to Docling's pictures on image content hash. Not worth the
complexity for a PoC, especially since real technical documentation usually
captions its figures visibly — which is the signal we actually want.

**A second Docling constraint shapes the design:** its built-in
picture-description enrichment appears to run for PDF only, not DOCX/PPTX
([docling#2225](https://github.com/docling-project/docling/issues/2225)) or
standalone images
([docling#2446](https://github.com/docling-project/docling/issues/2446)). So
caption *generation* is our own pipeline stage over the images Docling extracts,
rather than Docling's enrichment pipeline. Upside: the captioner model becomes a
free choice instead of one constrained by Docling's OpenAI-shaped API
integration.

- **Provenance:** record `extracted` vs `generated` per description. Cheap, and
  it lets the evaluation answer whether generated captions actually help
  retrieval or just add noise — the evidence that would justify upgrading the
  captioner.
- **Model:** start with Docling's default picture-description model. It is small
  and its captions are generic ("a bar chart") rather than factual ("return
  rates by product category, electronics highest at 12%"), and only the latter
  is retrievable. Accepted for now under the upgrade-on-evidence policy. The
  caption-first design also means it only runs on the minority of images that
  lack a visible caption.
- **Cache captions by image hash.** A few hundred images at CPU vision-model
  speeds is plausibly 30–60 minutes of ingest; re-running that every iteration
  would make development miserable, and hash-keyed caching fits the incremental
  ingestion design anyway.

### Image size

Model weights stack up, and a slow `docker compose up` works directly against
the smooth-install priority in requirements §5:

    BGE-M3                        ~2GB
    Docling layout + table models ~0.5GB
    OCR engine                    small
    picture-description VLM       0.5GB (default) .. 6GB (larger local model)
    torch (CPU)                   ~1GB

Mitigation regardless of the final numbers: bake model weights into the image at
build time so first run is fully offline and doesn't download at startup.

## Retrieval stack

### Vector DB — Qdrant

Candidates narrowed to Qdrant and Weaviate: both ship an official Docker image
and both advertise hybrid search. Chroma was dropped once BGE-M3 was chosen,
because the sparse-vector requirement rules it out.

**The decisive difference is what "hybrid" means in each product.**

- **Weaviate** hybrid = dense vector (bring your own) fused with **Weaviate's own
  internal BM25F** inverted index over object properties. The `hybrid()` query
  takes `query`, `vector`, `alpha`, `bm25_operator`, `query_properties` — there
  is no parameter for a precomputed sparse vector. You cannot feed it BGE-M3's
  sparse output.
- **Qdrant** treats sparse vectors as a first-class type, and the Query API
  fuses dense + sparse server-side in a single request via `prefetch` with RRF
  or DBSF.

Since BGE-M3 was chosen precisely *because* it emits dense and sparse from one
model, Weaviate would mean throwing half of it away — and with it the
justification for picking BGE-M3 at all.

Beyond that:

- **German breaks BM25.** Lexical matching works on surface forms, so a query
  for *Rücksendung* does not match *Rücksendebedingungen* without configured
  stemming and decompounding. Learned sparse vectors from a multilingual model
  match on semantics instead. With EN/DE as a hard requirement this is a real
  quality difference, not a theoretical one.
- **Embedded mode.** Qdrant runs in-process against `:memory:` or a local path,
  so unit tests can exercise real retrieval without Docker — the same instinct
  that kept Playwright out of the app image.
- **Named vectors** let a second embedding model live alongside the first in one
  collection, turning the possible BGE-M3-vs-smaller-model comparison into a
  re-query rather than a second ingest.
- Lighter: Rust single binary, smaller image, lower memory than Weaviate's Go
  runtime — relevant given how much the model weights already cost us.

**In fairness to Weaviate:** it is the more complete product — multi-tenancy,
RBAC, replication, built-in vectorizer modules — and its single `alpha` knob is
more ergonomic than composing prefetch clauses. None of that is load-bearing for
a single-user PoC over 65 documents, and it is more surface area to configure
and to explain.

**Gotcha to design around:** Qdrant point IDs must be unsigned integers or
UUIDs, not arbitrary strings. Deterministic chunk IDs therefore need hashing —
`uuid5` over (`doc_id`, `chunk_index`) stays deterministic, which is what makes
upsert-based incremental ingestion work.

**Worth stating explicitly: the DB and embedder decisions are coupled.**
Weaviate + BGE-M3 is the one combination that doesn't hang together. A coherent
Weaviate stack would be Weaviate + its BM25 + a dense-only embedder — at which
point e5-small becomes attractive again at a quarter of the size, and the
embedding decision below would need reopening.

### Embedding model — BGE-M3

Options considered: `multilingual-e5-small`, `multilingual-e5-large`, BGE-M3,
Cohere multilingual embeddings.

- **Cohere — excluded.** Free-tier rate limits make a reviewer's
  `docker compose up` unreproducible, and it adds a second API vendor plus
  another key to manage.
- **e5-small — considered, then rejected.** The initial instinct was the usual
  upgrade-on-evidence policy: start with the smallest model, which also keeps
  image size down. Rejected because it only covers the *dense* half of
  retrieval — pairing it with a separate BM25/lexical component to get hybrid
  search means more moving parts to build and maintain.
- **BGE-M3 — chosen.** Emits dense **and** sparse vectors from a single model,
  so hybrid retrieval works out of the box and there is no second lexical path
  to hand-roll. Multilingual and cross-lingual by design, which is what the ~20%
  EN/DE content overlap in the corpus is meant to exercise. 8k token input
  limit, so chunk size is not constrained by the embedder (e5's 512-token
  ceiling would have capped it).
- **Trade-off accepted:** ~2GB of weights and CPU inference, versus ~470MB for
  e5-small. Judged worth it for the code simplification.

This is the one place the upgrade-on-evidence policy was overridden — and the
reason was code simplicity rather than quality.

Note for a possible later comparison: switching embedder changes the vector
dimension (BGE-M3 is 1024-dim), which means recreating the Qdrant collection
rather than migrating it in place. Keeping the embedder behind an interface and
recording model name + dimension in the ingest manifest makes that swap cheap;
Qdrant's named vectors would allow A/B-ing two embedders over one ingest.

### Chunking — HybridChunker, ~512 tokens, neighbour expansion

Most of this decision turned out to be already solved by Docling, so the design
is mostly about *not* rebuilding what the chunker does: a tokenizer parameter
(point it at BGE-M3's own tokenizer so token counts are real rather than
estimated), two-pass split-then-merge on structural boundaries, table headers
repeated on overflow instead of truncation, and `contextualize()` which returns
a metadata-enriched serialization for the embedder. We embed that and keep raw
text for display. A useful side effect with hybrid retrieval: the heading path
lands in the **sparse** vector too, so lexical matches on section names work.

**Size — ~512 tokens.** BGE-M3 accepts 8k, so the model isn't the constraint;
retrieval quality is. One vector over a long passage averages across topics and
matches nothing strongly. Since re-ranking is deferred, retrieval precision
carries all the weight, which argues for the smaller end of the useful range.

**Retrieval unit ≠ generation unit.** Small chunks retrieve precisely but hand
the model fragments; large chunks ground well but retrieve poorly.

| Approach | Trade-off |
|---|---|
| Same unit for both | Simplest; fragments may lack context |
| **Neighbour expansion — chosen** | Retrieve the chunk, send it plus adjacent siblings. No side-store, predictable token cost |
| Parent-section expansion | Best grounding, but needs parent text stored outside the vector payload, and one large section can blow the latency budget |

Parent expansion was the initial choice and then dropped: it requires keeping
section text in a side store (storing it per-chunk would duplicate a section
once per child), plus a size cap and a fallback for oversized sections.
Neighbour expansion gets most of the grounding benefit with none of that, since
neighbours are just other chunks already in Qdrant, fetched by a payload filter
on (`doc_id`, `chunk_index` range) — no extra embedding work at query time. It
does need overlapping windows merged, and the window clamped to `parent_id` so a
neighbour from a different section can't mislead grounding.

This composes well with Claude's native citations: citations resolve to spans
*within* whatever block is sent, so an expanded window costs no attribution
precision. Broad grounding context and narrow attribution at the same time.

**Sequencing trap:** caption generation has to happen **before** chunking. The
chunker attaches captions to chunks, so a generated caption must be written back
into the `DoclingDocument` first. Get the order wrong and images that had no
visible caption produce empty chunks and the generation work is wasted.

### Re-ranking — deferred

Not in the initial build; revisit only if time allows. Consequence: retrieval
quality rests entirely on BGE-M3 hybrid search, so the accuracy evaluation is
what tells us whether that is good enough — it is the trigger for reconsidering.

This also removed re-ranking as a justification for the staged corpus batches
(+5, then +10). Those still earn their place by demonstrating incremental
ingestion.

## Generation

### LLM — Claude Haiku 4.5 to start

Upgrade-on-evidence again: cheapest and fastest first. It is also the best fit
for the ≤5s target, and for grounded extractive answering over retrieved context
the hard problem is retrieval, not generation — which is where the complexity
budget went.

Upgrade path is Sonnet 5, then Opus 5. Expect the ceiling to show up in
multi-hop synthesis across several chunks and in nuanced German phrasing, rather
than in simple extraction — so the golden Q&A set needs both, or the ceiling
stays invisible.

**Haiku 4.5 is an older-generation model and its request surface differs from
the newer ones. This matters because the upgrade is not a model-string swap:**

| | Haiku 4.5 | Sonnet 5 / Opus 5 |
|---|---|---|
| Thinking | `{"type": "enabled", "budget_tokens": N}` / `"disabled"` | `{"type": "adaptive"}`; `budget_tokens` → 400 |
| `output_config.effort` | errors | `low` … `max` |
| `temperature` | allowed | → 400 |
| Context | 200K | 1M |
| Prompt-cache minimum | 4096 tokens | 512 (Opus 5) |

Consequences:

- The latency dial is **not** `effort` here (it doesn't exist on Haiku) — it is
  thinking configuration.
- `temperature` is available, a genuine lever for the "predictable response
  quality" requirement — but it disappears on upgrade, so nothing load-bearing
  should depend on it.
- **Prompt caching may silently do nothing.** Haiku's 4096-token minimum is high
  and a system prompt plus guardrails may fall below it. It doesn't error;
  `cache_creation_input_tokens` just stays 0. Assert `cache_read_input_tokens >
  0` rather than assuming.
- Keep model configuration in one place so the swap is a config change, not a
  hunt through the codebase.

### Citations

Claude's native citations are used on the generation call: retrieved chunks go
in as `document` blocks with citations enabled, and the response carries spans
tied back to source chunks. This turns "high answer accuracy" from a claim into
a verifiable artifact, and gives the frontend clickable sources for free. It
also provides a downstream enforcement point for the knowledge-base guardrail —
an answer with zero citations can be replaced with the fallback message.

Note citations are incompatible with `output_config.format` within a single
call. That is not a conflict here, because the query rewrite (which does use
structured output) is a separate request.

### Guardrails — user input only

Injection defence applies to what the user sends. **Indexed documents are
considered safe for the PoC** and are not defended against. In production they
would be checked — retrieved content is attacker-controllable and would need the
same containment as user input, meaning delimited retrieved text and an explicit
instruction to treat it as data rather than instructions.

Recorded as a deliberate scope boundary, not an oversight.

One interaction worth noting: because conversation history is stateless and
client-supplied (below), the *history* is user input too — including assistant
turns, which a caller can forge. Guardrails therefore apply to every turn, not
just the newest.

## Orchestration

### Conversation history — stateless

The client sends prior turns with each request; there is no server-side session
store. A store would mean adding storage (an in-memory dict breaks the moment
more than one worker runs) for no PoC benefit, and statelessness keeps
horizontal scaling free. The costs are that the whole history must be validated
and guarded, and that turn count and total length need capping.

The LLM sees prior turns but **only the current turn's retrieved chunks** —
carrying previous turns' documents forward would grow context by roughly one
retrieval window per turn. Prompt order is system → history → retrieved
documents → question, keeping the volatile part last so the stable prefix stays
cacheable.

### Query rewriting — unconditional

A rewrite step runs before retrieval on every request, doing double duty:
resolving context-dependent follow-ups ("and what about returns?") and general
query improvement, which was wanted independently.

Conditional rewriting — only when history is non-empty — was considered, and
would have kept first turns free. Rejected because the query-improvement job
applies to every request, not just follow-ups.

- **Cost:** a second LLM call per request, **serial** and ahead of retrieval, so
  it lands directly on time-to-first-token.
- **Risk:** rewriting can drift from user intent and retrieve *worse* than the
  raw query would have.
- **Mitigation:** search on **both** the original and rewritten query as separate
  `prefetch` branches and let RRF fuse them, rather than replacing the original.
  The extra DB work is negligible next to the LLM call already being paid for.
- The rewrite call uses **structured outputs** so it reliably returns just a
  query string.

**Multi-turn is a nice-to-test, not a target.** History is supported, but
multi-turn behaviour isn't a graded goal — the golden Q&A set is single-turn.
The consequence to be aware of is that the follow-up path ships largely
untested.

## Performance and measurement

Both **time-to-first-token** and **total completion** are measured and
presented. The brief's "5 seconds" is ambiguous once responses stream, so
showing both is the honest answer, and which one gets emphasised depends on what
the data supports.

**TTFT is not cheap in this design.** Because the query rewrite is unconditional
and serial, first token only arrives after rewrite → embed → search → expansion
→ generation. In a plain chat app TTFT is near-instant; here it carries most of
the pipeline. So TTFT is not automatically the friendlier number.

That is the argument for **per-stage timers** rather than two endpoints. A
breakdown showing where the time goes, and which levers move it, is a stronger
result than a single headline figure — and it is the evidence base for three
deferred decisions at once: whether re-ranking's cost is affordable, whether the
rewrite call earns its place, and whether BGE-M3 on CPU is the bottleneck.

**Concurrency note:** the embedder and any local vision model are CPU-bound and
synchronous. Called directly from an async handler they block the event loop and
the concurrency requirement quietly fails under load. They need a thread pool
behind a bounded semaphore, or a separate process.

### Logging — two streams, split by file

Ordinary application logs and latency measurements answer different questions
and have different audiences, so they are kept apart rather than interleaved:

- `app` logger → **INFO**, console *and* `logs/app.log`. The things you would
  track for any app: requests in, requests out.
- `app.performance` logger → **DEBUG**, `logs/performance.log` only, with
  `propagate = False` so timing noise never reaches the general log.

`log_level` is a setting (`app/config.py`) and defaults to **DEBUG**, because
the latency breakdown is a deliverable of this PoC rather than an optional
extra.

**Timings are only measured at DEBUG.** `create_timings()` returns a no-op
collector when the performance logger is above DEBUG — one that makes no
`perf_counter()` calls at all. The instrumentation is genuinely off rather than
measured-and-discarded, so raising the log level in a latency-sensitive run
costs nothing. Stage names are free-form, so the stages still to be built
(rewrite, embed, search, expansion) need no change to the collector.

**Console output is kept alongside the files** so `docker compose logs` stays
useful. Writing logs to files inside a container would normally make them
invisible and short-lived — **for dev the container is mounted against the
working tree, so both files are written to disk on the host and remain
accessible after the container exits.** A production deployment would ship
stdout to a log collector instead of reading files off a volume.

## Security

**Secrets via `.env`**, read into the OS environment and consumed from there. No
credentials in source, satisfying the brief's mandatory requirement. `.env` must
be gitignored with a placeholder `.env.example` committed in its place. In
production this would be a secrets manager rather than a file on disk.

### API tokens — a demonstration, not authentication

The chat page embeds a short-lived signed token (HS256 JWT, 5-minute TTL) in a
`<meta>` tag; the frontend sends it as `Authorization: Bearer …` on every API
call, and `verify_token` checks signature and expiry.

**This is explicitly not security, because there is no auth.** Anyone who can
load the page is handed a valid token, so it establishes no identity and keeps
no one out — the brief does not require authentication (requirements §7.3) and
none is implemented. What it stops is the *casual* case: an API called directly
with no token at all.

What it does buy is that the mechanics real auth needs are in place and
demonstrated rather than described: a signed, expiring credential; verification
on every request; rejection as a flat 401 that leaks no reason to the caller
(the reason is logged instead); and a single `verify_token` dependency that any
future endpoint opts into with `dependencies=[Depends(verify_token)]`. Swapping
in real authentication becomes a change of *what the token asserts*, not a
rewrite of where it is checked.

Known limitations, stated rather than hidden:

- **The token is in the HTML**, so any XSS on the page can read it. With real
  auth this would be an `HttpOnly` cookie or an in-memory token from a login
  exchange.
- **No identity, no revocation, no rotation** — nothing to revoke, since every
  page render mints a fresh token.
- **The TTL is user-visible.** At 5 minutes a page left open will start getting
  401s; the frontend surfaces "Your session expired. Please reload the page."
  rather than a generic failure. A refresh endpoint would remove the friction
  and is the obvious next step if it becomes annoying.
- **`JWT_SECRET` is one value for the whole app.** Every process serving it must
  share the secret, or tokens minted by one are rejected by another — so it is a
  required setting rather than a per-process default.

## Verification spikes — deferred

Several open questions about Docling's behaviour — whether `PictureItem.image`
populates for DOCX/HTML, whether `HybridChunker` emits pictures as their own
chunks, whether the PDF-only picture-description limits still hold in the pinned
version — are deliberately **not** investigated up front. We react if problems
surface.

The caveat worth being explicit about: two of these fail **silently**. If
pictures aren't emitted as chunks, nothing throws — images simply never appear
in retrieval results. So error monitoring won't catch them; the evaluation will,
via the golden questions whose answers exist only inside a chart image. That
makes the eval the real safety net for this deferral, which is fine as long as
it runs before ingestion is considered finished.

## AI usage logging

Did not consider making the ai logging necessary work for another dev or other
ai tools than Claude.

Known limitation: `scripts/export_chat_log.py` (+ `.githooks/pre-commit`) only
captures Claude Code sessions. It satisfies this PoC's own AI-usage transparency
requirement (requirements §10), but it is not a general multi-tool/multi-dev
trace capture — another dev, or a different AI assistant, would need separate
tooling.

## E2E testing (Playwright)

Not baked into a dev Docker image — the browser + its system libs (libnspr4,
libnss3, etc.) only matter for running e2e tests, not for running/reviewing
the app itself, so it'd be dead weight in the main image for this PoC. If
CI or multi-machine dev parity becomes a real need later, the right shape is
a separate test-only Dockerfile/service, not bundling it into the app image.

To install and run locally:

    uv sync --group dev                      # installs pytest, pytest-playwright
    uv run playwright install chromium       # downloads the Chromium browser binary
    sudo uv run playwright install-deps chromium   # installs required OS shared libs (needs interactive sudo)
    uv run pytest -m e2e -v

The `install-deps` step needs interactive sudo (apt-get under the hood), so
it can't be run non-interactively/by an agent — a human has to run it once
per machine. See `.claude/skills/e2e-testing/SKILL.md` for locator
conventions used in these tests.
