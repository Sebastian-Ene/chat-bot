# Requirements

> Primary source: `docs/business-case.md` (the assignment brief). Supplemented by `docs/work.md` (own TODOs) and `docs/considerations.md` (own design notes). Fill in / correct as we go.

## 1. Overview
- What: a PoC customer-support conversational AI chatbot (RAG) that answers questions grounded in provided documentation.
- Context: this is a take-home assignment for an AI Solution Engineer interview. Deliverable is a single zip of the whole project; solution gets presented in a second interview.
- Emphasis (per brief): code quality, architectural reasoning, AI system design, and clear/explainable decisions — **not** feature completeness or UI polish. It's explicitly a PoC, not a production system.

## 2. Goals & Non-Goals
- Goals:
  - Answer customer support questions grounded in the provided documentation (no hallucinated/off-KB answers)
  - Ingest, process, and index docs (PDF, DOCX, HTML) into a local vector DB
  - Support English and German content
  - Demonstrate production-aware thinking (perf, security, observability) without needing to fully build it out
- Non-goals:
  - Full production system / full scalability
  - Full user authentication
  - Visual/UI polish
  - Streamlit (explicitly disallowed as frontend tech)
  - ai-usage logging tooling (`scripts/export_chat_log.py`) being reusable by other devs/tools — POC-only, Claude Code-specific (see `docs/considerations.md`)

## 3. Scope
- Languages: English and German
- Document formats: PDF, DOCX, HTML
- Document content: unstructured text, mixed layouts, embedded tables and images
- **Decision — corpus size:** documents are 1-25 pages each. Start with an initial corpus of 50 docs; later add a batch of 5, then a batch of 10, on top of the already-indexed set. The staged additions exist specifically to demonstrate:
  - incremental ingestion — adding new docs without re-processing the whole corpus
  - re-ranking — retrieval quality/ranking behavior as the corpus grows
- **Decision — design target:** even though the test corpus is small (65 docs total), the ingestion/indexing/retrieval design should be built to scale to much larger document volumes — this is for showcasing (production-aware thinking), not because the PoC itself needs that scale.
- **Decision — test document generation:** we generate all 65 documents ourselves (not provided), covering the three required formats (PDF, DOCX, HTML), each containing a mix of images, tables, and embedded info to exercise document understanding. Split ~50/50 English/German, with ~20% of the content overlapping in meaning across the two languages (same information expressed in both) — to test cross-lingual retrieval/grounding, not just per-language handling.

## 4. Architecture
- Required shape (per brief): a backend containing all AI/retrieval/orchestration logic, plus a frontend UI connected to it. Microservices allowed if they add clarity/value, not required.
- Vector DB must be **local** (not a managed cloud service).
- **Decision:** two containers via `docker-compose` — backend (uvicorn + FastAPI, serving the frontend too) and vector DB service — no load balancer. Priority is a smooth install for another dev: `docker compose up` should bring up the app with the vector DB already configured, no manual DB setup or Nginx layer needed. Drops the Nginx/LB from the original `docs/considerations.md` sketch as unnecessary for a PoC.
- Current implementation: minimal FastAPI app (`app/main.py`, `app/routers/pages.py`) serving one server-rendered HTML page — placeholder, not yet the real chat UI/API.
- Open: which local vector DB service to run in its own container (needs to be pick-and-justify anyway, see 5.2) — e.g. Qdrant or Weaviate ship an official Docker image, which is a factor in the choice.

## 5. Functional Requirements
### 5.1 RAG — Read (ingestion)
- Must ingest PDF, DOCX, HTML
- Must handle unstructured text, mixed layouts, embedded tables and images
- Document understanding technology is our choice (OCR, parsing, multimodal) — must be justified
- Open: pick the parsing/extraction approach (e.g. per-format libraries vs. a unified multimodal parser) and justify it

### 5.2 RAG — Store
- Vector DB: our choice, must be local — needs pick + justification
- Embedding model: our choice — needs pick + justification
- Chunking strategy: our choice — needs pick + justification

### 5.3 RAG — Generate
- LLM for retrieval/generation: our choice — needs pick + justification
- Integrate via API
- Prompt guardrails (mandatory):
  - Protection against prompt injection
  - Clear system instructions and role separation
  - Constraints to keep responses aligned with the provided knowledge base
- Must deliver high accuracy, consistent/reliable behavior, predictable response quality

### 5.4 Backend
- Contains all AI, retrieval, and orchestration logic (FastAPI, per own notes — justify choice)
- Must support concurrent access (multiple simultaneous users)
- Must implement measurements: logging, timing, metrics for performance
- Must stream responses to the frontend
- Target: a single completion should not exceed 5s under normal conditions (perfect optimization not required, but design should show performance awareness)

### 5.5 Frontend
- Any HTML-rendering technology allowed; **Streamlit is explicitly disallowed**
- Must provide a simple chat interface
- Must support streaming responses from the backend
- Minimal/functional is sufficient — no visual polish required
- **Decision:** plain HTML + vanilla JS, served by the existing FastAPI + Jinja2 setup (`app/templates/`). A small JS chat widget reads a streaming response (SSE or fetch-stream) from the backend. No build step, no separate frontend service/container — one backend container serves both API and UI, consistent with the "smooth install" architecture decision (§4). No framework (React/Vue/htmx) needed given the PoC doesn't require UI polish.
- **Implemented:** `app/templates/index.html` + `app/static/{style.css,chat.js}` — chat log, input, send button, streamed via `fetch`. `/api/chat` doesn't exist yet, so replies currently show an error bubble. Elements use explicit accessible names/roles (not ids/classes) for stable e2e targeting. Fixed post-implementation: dark-mode bubble contrast, title scrolling out of view on long conversations, and replies not scrolling into view — all covered by e2e tests (§7).

## 6. Non-Functional Requirements
### 6.1 Quality / Accuracy
- High answer accuracy, consistent/reliable behavior, predictable response quality (mandatory, no specific metric given)

### 6.2 Performance
- Concurrent multi-user access
- Single completion ≤ 5s under normal conditions
- Logging/timing/metrics required to demonstrate performance awareness

### 6.3 Security
- Full user authentication **not required**
- Mandatory: proper API key and secret management, no hardcoded credentials in source
- Any additional security measures taken should be documented

## 7. Testing Strategy
- No specific testing methodology is mandated by the brief — emphasis is on architectural reasoning over feature completeness, so this is our call
- Open: how do we demonstrate "high accuracy" / "consistent behavior" — a small golden Q&A set + manual/LLM-judge eval, or is documented reasoning enough for a PoC?
- **Implemented — UI e2e tests:** Playwright (`pytest-playwright`), `tests/e2e/`, run against the real app via a `live_server` fixture. Locators use accessible roles/names/text only, never ids/classes (see `.claude/skills/e2e-testing/SKILL.md`). Not baked into a dev Docker image — install/run steps documented in `docs/considerations.md`.
- **Decision — performance testing:**
  - A test suite that issues single prompts and asserts each completes in under 5s, demonstrating the target constraint is met, not just assumed.
  - A lightweight concurrency test (a handful of concurrent simulated users) showing performance doesn't degrade unacceptably under light concurrent load — enough to back the "supports concurrent access" requirement with evidence, without a full load-testing setup (e.g. no locust/k6 needed).

## 8. Deployment / Packaging
- Final deliverable is a **single zip file** of the whole project — no live deployment target is required
- **Decision:** ship a `docker-compose.yml` with a backend service (built from this repo) and a vector DB service, so another dev can run the whole thing with one command and no manual DB configuration. This is our own addition (`docs/work.md`) beyond the brief's minimum, chosen to demonstrate production-aware packaging and an easy reviewer experience.
- `uv` is still used for local (non-Docker) dev — the Docker image should also build via `uv` for consistency.

## 9. Documentation & AI Usage Transparency (mandatory deliverables)
- Architecture overview
- Key design decisions and trade-offs
- Chosen models, tools, and technologies
- **Must use an AI assistant during implementation**, and must include:
  - All prompts used during development
  - Relevant LLM interaction traces that contributed to the final solution
  - This is what `scripts/export_chat_log.py` + `.githooks/pre-commit` exist for — auto-exports Claude Code transcripts into `chat-logs/` per commit
  - **Decision:** document this as a known limitation — the capture tooling only supports Claude Code sessions (per `docs/considerations.md`: "did not consider making the AI logging necessary work for another dev or other AI tools"), not a general multi-tool/multi-dev trace capture. Sufficient for this PoC's own AI usage transparency requirement; call it out explicitly rather than implying broader support.

## 10. Open Questions
- Which local vector DB to run in Docker (candidates should ship an official image, e.g. Qdrant/Chroma/Weaviate) — **deferred, TBD**
- Parsing/extraction approach for PDF/DOCX/HTML with tables, images, mixed layout, bilingual content — **deferred, TBD**
- Embedding model — **deferred, TBD**
- Chunking strategy choice — **deferred, TBD**
- LLM choice for generation/retrieval — **deferred, TBD**
- How to demonstrate/measure accuracy and reliability — **deferred, TBD**

~~Architecture shape (LB vs. simplified)~~ — resolved: docker-compose with backend + vector DB containers, no LB (see §4).
~~Docker vs. plain zip~~ — resolved: keep Docker for easy install, see §8.
~~Frontend approach~~ — resolved: plain HTML + vanilla JS served by FastAPI, no separate frontend app (see §5.5).
~~Claude-Code-only trace capture~~ — resolved: document as a known limitation, not a general capture tool (see §9).
~~Expected document volume/corpus size~~ — resolved: 65 docs (50 initial + 5 + 10 staged), 1-25 pages each, designed to scale further for showcase (see §3).
~~Source of the test documents~~ — resolved: we generate all 65 ourselves, PDF/DOCX/HTML mix with images/tables/embedded info, ~50/50 EN/DE with ~20% cross-lingual content overlap (see §3).
~~Load testing scope~~ — resolved: single-prompt latency tests (assert <5s) plus a lightweight concurrent-users test, no full load-testing harness (see §7).
