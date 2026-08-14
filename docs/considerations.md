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
PoC. Priority is a smooth install for another dev: `docker compose up` should
bring up the app with the vector DB already configured (requirements §5).

### Ingestion runs in its own container, as a job

Two services — **api** and **qdrant** — plus an **ingest** job.

Docling is needed only for ingestion — parsing and chunking both happen there,
and no request path touches it. Ingestion is minutes of pinned CPU; sharing a
container with the API means one ingestion run degrades every in-flight chat
request, against a brief that mandates concurrent access and a 5 s completion
target. Separating the processes answers that better than a semaphore does.

The API keeps BGE-M3 for query embedding, so it is **not** a thin container —
507 MB before, ~7 GB after, since the model brings torch with it. That is the
price of choosing one model to emit both dense and sparse vectors: the model has
to exist wherever a vector is produced, and index-time and query-time embedding
must stay identical or retrieval silently degrades.

The alternative is an **embedder service** both the api and the job call: BGE-M3
stored once instead of twice, the api back to 507 MB with a fast rebuild, and
the model scaled — or GPU-placed — independently of a request path that is
otherwise IO-bound. It is the better production shape and it was not built here:
a third service and an HTTP contract buy nothing on one machine, where the hop
costs more than it saves and in-process embedding already answers in 33 ms.

**Ingestion is a job, not a service** — `docker compose run --rm ingest`. It
runs to completion, is started by an operator or a schedule, and takes minutes;
nothing remote needs to start a run, since documents arrive by being placed in
the corpus directory and whoever can do that can run a container. In production
the documents would more likely sit in object storage, with the run started by
an update hook.

The corpus directory is a volume mounted by the api and the job.

The api image installs main dependencies only (`uv sync --no-default-groups`),
so **Docling is absent from it** — the layout, table-structure and OCR models
are the larger half of the 18.3 GB ingest image, and no request path touches
them. A test asserts the boundary holds (`tests/api/test_image_boundary.py`), so
an accidental import fails the suite rather than the container.

### Source is bind-mounted in dev, baked into the image elsewhere

The api container mounts `./app` and `./logs` from the host, so code is
live-editable under `--reload` and logs are readable without entering the
container.

That is a **development** choice, not the shipping shape. An upper environment
runs the code baked into the image — no source mount, no `--reload` — so what
was tested is what runs and the container stays immutable. The mount and the
reload flag therefore belong in an environment-specific compose overlay; the
split is deferred while there is only one environment.

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

### Corpus size — ~25 documents

Sized by what makes retrieval measurable. With 5 documents recall@5 is 100% by
construction, so no retrieval decision can be evaluated; enough distractors to
make the wrong chunk competitive is what sets the floor. Past ~25 is scale
without new capability, and the effort is better spent on the eval harness.

Hence two standards: coverage documents hand-authored, distractors authored as
data through a shared renderer — with several structural variants, since one
renderer for everything gives the corpus a single layout fingerprint.

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
  Ingest is offline, so it never touches the 5s completion target. Measured: the
  venv grows to **5.4 GB** with torch and transformers, before any model weights.

**`TORCHDYNAMO_DISABLE=1` is required.** torch tries to JIT-compile through
inductor/triton, which needs a C compiler; without one every conversion fails
with `Failed to find C compiler`. Ingest is offline, so the eager path costs
nothing that matters. Set it before torch is imported.

Docling's `HybridChunker` also turned out to settle most of the chunking
decision — see below.

### OCR — kept on

The corpus is digital-native, so OCR isn't needed for page text and switching it
off would be a free speedup. Kept on anyway because OCR reads text rendered
*inside* images — chart axis labels, legends, numbers baked into diagrams —
which the captioner does not reliably transcribe. The two complement each other
on exactly the figures that matter.

### Images — describe every figure from its pixels

Goal: every image ends up with an indexed, referenceable text description.

This started as caption-first — reuse `PictureItem.captions`, the visible
"Figure N: …" text, and generate only for figures without one. That was
abandoned once the evidence arrived: a caption names what a figure *is*, and
retrieval needs what it *contains*. Both questions the figures exist to answer
(`qa-005`, `qa-007`) need values that appear nowhere but inside the image, so a
caption would have short-circuited exactly the figures that needed describing.
Every figure is now described from pixels. The reasoning that shaped the rest of
the design is kept below, since the Docling constraints it records still hold.
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

What was built (`ingestion/describe.py`) differs from the caption-first sketch
above on one point, deliberately:

- **Always describe from pixels — never short-circuit on an embedded caption.**
  A caption says what a figure *is*; retrieval needs what it *contains*. The
  caption on the installation-guide wiring diagram would not have answered
  `qa-005` or `qa-007`, whose values exist only inside the image. Describing
  every figure costs one vision call each, once, and the cache makes it a
  one-off — a small price for answers that are otherwise unreachable. It also
  removes the `extracted` vs `generated` provenance split, since everything is
  generated.
- **Model:** Claude vision (`describe_model`, Haiku by default) rather than a
  local VLM. The local models are not installed and would add 0.5–6 GB to an
  18.3 GB image; more decisively, their captions are generic ("a bar chart")
  where only the factual form is retrievable. Prompted to transcribe series
  values, not to caption.
- **Cache by image hash.** Re-ingestion and `--force` re-describe nothing, which
  matters because parsing already dominates a run at ~180 s.

### Spike results — what Docling actually gives us

Measured against the real corpus (`scripts/spikes/`), not assumed. Three findings
contradict the design as written.

| Format | Image bytes | Caption associated |
|---|---|---|
| PDF | yes (`get_image` → PIL) | yes, but see below |
| DOCX | yes | **no** |
| HTML | **no** (`image` unset) | no |

- **HTML figures yield no pixels.** Docling finds the `PictureItem` but carries
  no image, so caption generation cannot run for HTML through Docling. Resolving
  the `<img src>` against the document's directory and reading the file ourselves
  is the only route — a format-specific path in a deliberately unified parser.
- **DOCX captions are not associated.** A visible "Figure 1: …" paragraph comes
  back as `caption=''`, so every DOCX figure falls to the generation path
  regardless of what the document says. Reading the DOCX XML ourselves is the
  only fix, which is the second-parse complexity rejected for alt text.
- **A PDF caption is not always the caption.** With OCR on, the wiring diagram
  returned text from *inside the image* rather than its real caption. So
  "captions non-empty" does not mean "the document captioned this figure", and
  provenance `extracted` can silently record OCR output.

Chunking behaves as hoped: pictures **do** reach the chunker (one `picture`
chunk, merged with its surrounding prose), `contextualize()` prepends the heading
path, and a description written onto the picture reaches the chunk text — so
generated captions will be indexed. Write it to **`PictureItem.meta`**
(`PictureMeta.description`, with `created_by` carrying provenance);
`annotations` still works but is deprecated in docling-core 2.91.

Two smaller consequences: `pages` is 0 for DOCX and HTML, so the `page_no`
payload field only ever populates for PDF; and the page-spanning table arrives as
**two** table objects rather than one.

### Image size

Model weights stack up, and a slow `docker compose up` works directly against
the smooth-install priority in requirements §5:

    BGE-M3                        ~2GB
    Docling layout + table models ~0.5GB
    OCR engine                    small
    picture-description VLM       0.5GB (default) .. 6GB (larger local model)
    torch (CPU)                   ~1GB

Model weights live on a named cache volume, so they download once and survive
container recreates.

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
a single-user PoC over a corpus this size, and it is more surface area to configure
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
recording model name + dimension alongside the index makes that swap cheap;
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
| **Neighbour expansion — chosen, not built** | Retrieve the chunk, send it plus adjacent siblings. No side-store, predictable token cost |
| Parent-section expansion | Best grounding, but needs parent text stored outside the vector payload, and one large section can blow the latency budget |

Parent expansion was the initial choice and then dropped: it requires keeping
section text in a side store (storing it per-chunk would duplicate a section
once per child), plus a size cap and a fallback for oversized sections.
Neighbour expansion gets most of the grounding benefit with none of that, since
neighbours are just other chunks already in Qdrant — and because point ids are
`uuid5(doc_id, chunk_index)`, they are fetched by key rather than by a filtered
scan, with no extra embedding work at query time. It does need overlapping
windows merged, and the window clamped to `parent_id` so a neighbour from a
different section can't mislead grounding.

**It is designed and deliberately not built.** Retrieval finds the right
document for 18 of 18 golden questions, so there is no observed failure that a
wider window would fix, and expansion would roughly triple the context tokens to
buy it. The trigger is an eval case that answers wrongly *because the chunk was
a fragment* — the same rule applied to the captioner and to re-ranking: measured
failure, not preference. `parent_id` is already in the payload, so the work is
ready to start the moment such a case appears.

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
- **Prompt caching does nothing here.** Only the prefix shared between requests
  can cache, and that is the ~264-token system prompt — the documents and
  question are per-request. Far under Haiku's 4096 minimum, so no `cache_control`
  is set. It would not error if it were; `cache_creation_input_tokens` would
  just stay 0.
- Keep model configuration in one place so the swap is a config change, not a
  hunt through the codebase.

### Citations — not built

Claude's native citations would have made attribution verifiable: chunks as
`document` blocks, spans tied back to source. Dropped as out of scope — chunks
go in flattened, and the system prompt tells the model not to name the reference
documents. Provenance lives in the logs (`RetrievedChunk.citation()`) only.

Cost of the choice: no clickable sources, and no place to enforce the
knowledge-base guardrail downstream (an answer with zero citations could
otherwise be swapped for the fallback).

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

### Guardrails — what is actually implemented

Two layers, deliberately different in kind (`api/rag/guardrails.py`):

**1. Sanitising — deterministic, always applied.** Our prompt uses
`<reference_documents>` and `<user_message>` as structure. Without this, a user
could type `</reference_documents>` and have their text read as prompt
structure. `sanitize()` escapes the angle brackets of *our* reserved markers
only, so the user's words survive and their structural power does not. Ordinary
angle brackets (`3 < 5`, `<div>`) are untouched.

**2. Detection — heuristic, logs only, never blocks.** A small named pattern set
covers the classic shapes (ignore-previous-instructions, role override, prompt
disclosure, jailbreak, injected directives). It deliberately does **not** reject
the request: the patterns match plenty of legitimate questions ("ignore the first
document, what does the second say?"), and blocking a real user to catch a string
match is the wrong trade. Matches are logged by pattern name — never the user's
text, which may contain anything.

**3. The system prompt** carries §6.3's three mandates: role separation (this
prompt is the only source of instructions), an explicit statement that everything
in the conversation is client-supplied data rather than instructions, and the
knowledge-base constraint (answer only from the reference documents; say so when
they don't cover it).

**Scope is user input only** (§6.3), which means the question *and every history
turn*, assistant turns included — those are client-supplied and forgeable.
Retrieved context is deliberately **not** sanitised: indexed documents are
trusted for this PoC, and escaping them would corrupt document text.

**Forged assistant turns.** Statelessness (§6.4) means a caller can put any words
in the assistant's mouth, and a model is inherently inclined to trust its own
prior turns. Sanitising and prompt hardening shrink the blast radius; they do not
close it.

The answer here is the analysis call, which judges the **whole conversation**
rather than just the latest message. It marks a request unsafe
(`forged_history`) when a prior assistant turn issues instructions, claims the
rules or mode have changed, or otherwise reads as something a support assistant
would not have written — so a benign-looking question trading on a forged turn is
refused before retrieval and generation.

The honest limit: this is **judgment, not integrity**. The system cannot tell a
real assistant turn from a fabricated one; it can only notice when a fabricated
one looks wrong. A subtly-worded forgery can still pass.

Heuristic regex detection is likewise trivially evaded by rephrasing; it is an
observability signal, not a control.

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

### What the rewrite produces — and what is unproven

The rewrite emits a standalone query, plus two extra retrieval branches:
**keywords** (salient nouns for the lexical/sparse side) and **sub-queries**
(only for genuinely multi-part questions). Every populated field becomes its own
`prefetch` branch, RRF-fused, with the **original query always surviving fusion**
— so a rewrite that drifts cannot retrieve worse than the raw query alone. The
prompt forbids inventing product names, numbers or constraints, and tells the
model to return the question unchanged when it is already standalone.

**Cross-lingual is left to the dense side.** A translated branch was considered
and dropped: BGE-M3 is multilingual, so dense retrieval should carry EN↔DE on its
own. The sparse branch stays language-bound as a result, which is a known,
accepted gap — worth revisiting if the eval harness shows cross-lingual recall
lagging.

**Keywords and sub-queries may well be noise.** Both are reasoned improvements,
not measured ones — there is no corpus, no golden set and no recall@k yet, so
neither can currently be shown to help. Keywords may add little over what the
sparse encoder already extracts; sub-queries risk fragmenting a question one
search would have answered. Both sit behind `REWRITE_KEYWORDS_ENABLED` and
`REWRITE_SUB_QUERIES_ENABLED` precisely so they can be A/B'd and dropped once a
minimal testing corpus exists. Disabling a flag removes the field from both the
schema and the prompt, so a disabled branch costs no output tokens.

### Safety verdict and rewrite share one call

The rewrite call also returns a safety verdict (`api/rag/query_analysis.py`):
`{safe, category, rewritten_query}` from a single structured-output request.

**Why merged:** both jobs need the same input (question plus history) and both
must run before retrieval. Two serial calls would put two round trips ahead of
the first token, on a budget that §7.2 already identifies as tight. One call
does both.

**Why an LLM check on top of `api/rag/guardrails.py`:** the regex heuristics there
are trivially rephrased around, and they deliberately never block. A model
judging intent in context is a much better signal — good enough to act on.

**Fail closed.** Anything that leaves us without a usable verdict — API error,
malformed JSON, a field of the wrong type — refuses the request rather than
falling through to retrieval and generation. The parsing model is **strict**:
pydantic would otherwise coerce `{"safe": "yes"}` into `True`, and a verdict we
had to guess at is one we should not act on.

The costs of that choice, taken deliberately:

- **The classifier becomes a hard dependency.** An API blip now refuses the
  request before retrieval, where previously only generation failed. The SDK's
  default two retries on 429/5xx soften this, but it is a real availability
  trade.
- **False positives have no appeal path.** A wrongly-refused user can only
  rephrase. The refusal is logged at WARNING with the category so the rate is
  observable.
- Refusals and failures are deliberately **different messages**: someone who
  asked a legitimate question should not be told they misbehaved because we
  broke. Both stream back as a normal 200 — they are content decisions, not
  protocol errors.

**The classifier is itself an injection target,** so the question and history are
sanitised through `api/rag/guardrails.py` before reaching it, and its system prompt
states that a message asking to be marked safe is itself unsafe.

**Not cached:** the classifier prompt is well under Haiku 4.5's 4096-token
prompt-cache minimum, so a `cache_control` breakpoint would silently no-op.

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

`log_level` is a setting (`common/config.py`) and defaults to **DEBUG**, because
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

### Ingestion has no network surface to defend

Nothing listens, so there is nothing to authenticate, rate-limit or lock.
Starting a run requires the ability to run a container — already a higher
privilege than any credential we could have issued for it.

What remains:

- **No path argument** — the root is the `CORPUS_DIR` setting, fixed at startup,
  so a run cannot be aimed at arbitrary files on the host.
- **Corpus mounted read-only** — the job parses documents, it never writes them.
- **Outbound egress since figure description.** Nothing listens, but the job now
  *sends*: figure images go to the Anthropic API to be described, so document
  content leaves the machine and ingestion is no longer fully offline. The key
  is optional (`IngestSettings.anthropic_api_key`), so an air-gapped run stays
  possible by omitting it — figures are then skipped and the run still
  succeeds. For a corpus with confidential figures, that is the switch to use.

### API tokens — a demonstration, not authentication

The chat page embeds a short-lived signed token (HS256 JWT, 30-minute TTL) in a
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
- **The TTL is user-visible.** A page left open past 30 minutes starts getting
  401s; the frontend surfaces "Your session expired. Please reload the page."
  rather than a generic failure. It started at 5 minutes, which expired in the
  middle of ordinary use — the fix for that is a refresh endpoint, and a longer
  TTL is the stand-in until there is one.
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

## Known issues

Accepted limits of the PoC, not defects. Each is a deliberate deferral with the
condition that would make it worth paying for.

### 1. No real data

The corpus is synthetic — generated by `scripts/generate_corpus.py` to exercise
formats, languages and layouts. Real documents bring inconsistent structure,
scans, revisions and contradictions between sources. Every parsing and
retrieval number here is measured against a corpus that was built to be
tractable.

### 2. Small, weak golden set

51 questions written alongside the corpus, so they inherit its blind spots —
authored by the same hand that knows where the answers live. Enough to catch
regressions, not to establish accuracy. A real set is written from user
questions, by someone who did not build the index.

### 3. No re-ranking

Fusion output goes straight to the model. Nothing checks that a chunk *answers*
the question rather than resembling it, which is precisely what over-answering
is made of (#10) — so this is no longer a corpus-size argument, it has a
measured trigger.

**Five relevant chunks beat ten that might include misses.** Raising
`retrieval_top_k` to 10 bought answerable coverage and paid for it in
fabrication: every extra chunk is more plausible-but-wrong material to assemble
from. A cross-encoder over the top ~50 lets the cut go back down to ~5 while
keeping the recall, which is the trade the other way round.

What it costs, in order:

- **Compute shape changes.** Cost moves off LLM calls and onto re-ranking — a
  second model in the request path, one that scores every candidate rather than
  embedding one query.
- **Which argues for splitting model inference into its own service.** Two
  models in the api container already make it the fat unit; a third makes
  scaling the request path mean scaling GPU-shaped work with it. Separate
  services let retrieval, re-ranking and the web tier scale on their own curves
  — the same argument as the embedder service, but with enough weight behind it
  to be worth the split.
- **Latency may break the 5 s target.** Re-ranking 50 candidates is not free,
  and total p95 is already 4.97 s.
- **Then the query-rewrite call is what to reclaim it from.** Analysis is 1.27 s
  median, the single largest stage after generation, and it is one LLM call on
  the critical path of every request. Dropping or shrinking it — a smaller
  model, or rewriting only when the question looks context-dependent — is where
  the budget for re-ranking comes from.

### 4. Docker setup is development-shaped

The images themselves are reasonable — multi-stage, non-root, healthchecked,
code baked in. What is not production-ready is how they are *run and sized*:
`docker-compose.yml` bind-mounts `api/`, `common/` and `ingestion/` over the
baked copies and runs uvicorn with `--reload`, so the image contents are not
what executes. Both images also bake BGE-M3 (api ~16 GB), which is the right
call locally — a first request that downloads 2.3 GB is a timeout, not a warm-up
— and the wrong one for a registry.

Production would drop the mounts and `--reload`, pin the base image and
`ghcr.io/astral-sh/uv:latest` by digest, and move the models to a shared volume
or an init container rather than shipping a copy inside every image.

### 5. No database behind the api

The api is stateless: history arrives from the client on each request and is
never persisted. That blocks server-side sessions (the client can forge history
— hence guarding assistant turns), and it blocks the whole analytics loop.
Nothing accumulates about which questions get asked, which get refused, or which
retrieve badly, so improvement stays anecdotal.

### 6. No multi-turn evaluation

Every golden question is single-turn. A larger corpus invites questions that
reference earlier answers, and evaluating those means driving multi-step
conversations — agentic harness, tool development, and far higher eval cost per
run than the current single-shot pass.

### 7. No neighbour expansion

A chunk is sent as retrieved, never widened to its siblings. Corpus-size
dependent, like re-ranking: it matters when an answer needs more context than
one chunk holds *and* the adjoining chunk did not make the cut. Raising
`retrieval_top_k` to 10 covers the cheap end of that. `parent_id` is in the
payload and neighbour ids are computable from `uuid5(doc_id, chunk_index)`, so
the work is ready to start — `point_id()` has to leave `ingestion/index.py`
first, since that module imports docling and must not reach the api.

### 8. No rate limiting

`/api/chat` is public and unmetered. Every message costs an analysis call
*before* anything can refuse it, so an attacker generates real spend with no
accumulating penalty — a refused message is kept out of the history, so retrying
from a clean conversation costs them nothing. The page token is a demonstration,
not authentication, and does not bound this.

The fix is not a limiter bolted onto an open endpoint: it is real user
authentication, the api no longer publicly reachable, and a per-user limit on
top. Accepted for a PoC that is not deployed.

### 9. No linting, type checking, CI or coverage

Ruff, mypy, pre-commit, CI and coverage reporting are all absent — they buy
consistency and safe collaboration rather than working software, which is why
they lost to features on a timed solo PoC and would not on a team.

### 10. Declining is weaker than answering

Answerable questions score **42/42**; must-decline questions score **5/9**. Four
were answered with a fabricated specific lifted from adjacent context: `qb-025`
priced express delivery to Belgium at €59 (the free-shipping *threshold*, not a
price), `qa-103` invented a "under 1 second" response time for a maintenance
tier, `qa-101` a retention policy, `qa-105` an automation limit.

The number is always sitting next to the question in the context. Raising
`retrieval_top_k` to 10 doubled how much of that there is — the same change that
took answerable from 40/42 to 42/42, so it is the price of coverage rather than
a regression to undo.

Being wrong costs most on this axis: a confident fabricated figure is worse than
a wrong answer to an answerable question, because nothing in the reply signals
doubt. The fix is re-ranking (#3); the cheaper half-measure is a system prompt
demanding the answer be *stated* in the documents rather than derivable from
them.

### 11. Safety refusals are non-deterministic

`qa-016`, a benign German troubleshooting question, was refused as
`harmful_content` on one run and answered correctly on the next, with no change
to the system. Retrieval had the right chunk at rank 1 both times; the
classifier never let it through on the first.

Distinct from the invented-category bug that was fixed — this is a real category
applied to a benign question, which a closed set cannot prevent. A false refusal
accuses the user of something, so it is the worse failure mode.

Intermittent, so the metric is the refusal rate over runs, not the case. Levers:
a lower-variance model for the safety verdict, few-shot examples of
benign-but-alarming phrasing, or splitting the verdict off the rewrite call so
each prompt does one job — which the latency work in #3 may force anyway.

## Improvements

Measured failures and their fixes; speculative ideas go in `docs/work.md`. One
line each, heading tagged `fixed` / `open`:

- **Broke** — the symptom, and what surfaced it
- **Why** — the cause
- **Fix** — what changed
- **Left** — residual risk or the next lever; omit when there is none

### Safety classifier invented a refusal category — fixed

- **Broke** — `scripts/eval_golden.py`: a benign shipping question refused as
  `category=unclear_scope`, not one of the four the prompt names. Fails closed,
  so it never reached retrieval.
- **Why** — nothing told the model the category list was closed.
- **Fix** — the prompt names the four as a closed set, and marks unclear or
  undocumented questions safe: "not in the documentation" is retrieval's answer
  to give, not the classifier's.
- **Left** — intermittent (Haiku), so watch the refusal rate, not the case. A
  schema `enum` on `category` would make invention impossible.

### Table answers read the neighbouring row — intermittent

- **Broke** — `qa-001`: business returns answered "no restocking fee"; the row
  below says 15% for opened-but-complete. Twice running, then correct on the
  third with the same document at rank 1.
- **Why** — unsettled. Chunking flattens the table and `doc3_warranty.py` keeps
  these values in a table only, so a neighbouring row is easy to pick up; but
  two identical failures were not enough to call it deterministic, and the
  shorter analysis prompt landed between run two and run three.
- **Fix** — none, deliberately. Watch it: if it recurs, keep table rows
  addressable through chunking rather than flattening them.
- **Left** — the other 7 `table_only` questions pass throughout, so this is row
  precision at worst, not table handling in general.

### Figure data points are unreachable — fixed

- **Broke** — `qa-005` (battery ~40 % at 15 months) and `qa-007` (busiest
  weekday) both declined. A figure with no caption and no description is
  *dropped entirely*: the battery PDF produced 11 chunks and none was the chart.
- **Why** — no description stage, so nothing existed to merge into prose. OCR
  reads text *inside* figures, but a plotted point is not text; and HTML figures
  never reached the pipeline at all, since Docling carries no image bytes for
  them.
- **Fix** — `ingestion/describe.py`: Claude vision through Docling's
  `PictureDescriptionApiOptions` + `api_image_request` against Anthropic's
  OpenAI-compatible endpoint, written to `PictureItem.meta` before chunking and
  cached by image hash. Prompted to transcribe series values, not caption.
  Driven by us rather than Docling's enrichment, which is PDF-only; HTML figures
  load from `<img src>`. Both questions now answer correctly.
- **Left** — descriptions are searchable text, not a data source: the series
  `qa-005` needs came out exactly, but a neighbouring series drifted 1–3 points
  and one annotation was attributed to the wrong curve. Ingestion now takes an
  optional `ANTHROPIC_API_KEY`; without it figures are skipped and the run still
  succeeds. Anthropic documents the compatibility layer as not production-ready.

### An over-strict judge outscored the system it graded — fixed

- **Broke** — the harness reported 18/21 where the app had answered 21/21: it
  marked correct answers wrong for adding accurate detail and for a well-formed
  decline, both explicitly allowed by the rubrics.
- **Why** — the judge had been moved to `claude-haiku-4-5` for cost.
- **Fix** — back to `claude-opus-5`, with a comment saying why. 26 calls per
  eval; cost is not a reason to downgrade it.
- **Left** — an LLM judge is still a measurement instrument with its own error.
  Read the reasons on any verdict that surprises you before believing the score.

### Conditional answers lose a branch at k=5 — fixed

- **Broke** — `qb-014` (free-shipping thresholds) and `qb-015` (consumer return
  window) each answered from one branch only, giving the general policy and
  dropping the regional exceptions. The two `conditional` misses were the only
  retrieval failures in set 1 (`conditional 1/3`).
- **Why** — not ranking: coverage. Both answers span three documents, and the
  top 5 held duplicates — the UK addendum twice, the general policy twice —
  leaving three effective slots for three required documents.
- **Fix** — `retrieval_top_k` raised from 5 to 10. `retrieval_prefetch_limit` is
  already 20, so the candidates exist and only the cut changes. Chosen over
  neighbour expansion, which is the same fix by a longer road: keyed sibling
  lookups, window merging, clamping to `parent_id`, and moving `point_id()` out
  of `ingestion/index.py` first. Doubling k is one setting.
- **Left** — verified: both now answer correctly and every answerable question
  passes, 42/42. Median input tokens went 2 100 → 2 747 and total latency p95 is
  4.97 s, inside the 5 s target. The cost landed elsewhere — see
  *Over-answering* below, where the wider context gives more plausible-but-wrong
  material to assemble from.

### Answer assembled from unrelated rows — superseded

`qa-101` built a retention policy out of error-code rows K564–K568 that merely
mention a 30-day window. It was the first instance of what is now **Known issues
#10** — three more cases have since appeared, and the analysis lives there.
