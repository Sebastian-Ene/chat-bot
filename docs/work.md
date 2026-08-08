# TODO

> Reorganized to follow `docs/requirements.md`. Decisions already made there are turned into concrete tasks; still-open items (§10) stay as "decide:" tasks. Backend/frontend come first, built against mocked RAG/LLM responses, so RAG internals can be swapped in later without blocking the rest of the stack.

## Setup
- ~~Create a proper py project~~
- ~~Add a project description for AI~~

## Backend
- ~~Create b-e with Python (FastAPI, chosen for async performance)~~
- Mock RAG/LLM responses (fake retrieval + fake streamed completion) so the API contract exists before real RAG is wired in
- Chat endpoint(s) serving the mocked responses, streamed
- Logging / timings / metrics for performance
- API key and secret management (no hardcoded credentials)
- Document any additional security considerations

## Frontend
- ~~Turn `app/templates/index.html` into an actual chat interface (plain HTML + vanilla JS, per requirements §5.5)~~
- ~~JS chat widget consuming a streaming response (fetch-stream) — targets `/api/chat`, not built yet so replies show as an error bubble for now~~
- ~~Fix accessible color contrast on chat bubbles~~
- ~~Fix chat title scrolling out of view during long conversations~~
- ~~Fix conversation log not scrolling to reveal the latest reply~~

## Test document corpus
- Generate 50 initial docs: PDF/DOCX/HTML mix, 1-25 pages each, unstructured text + mixed layouts + embedded tables/images, ~50/50 English/German, ~20% cross-lingual content overlap
- Generate a follow-up batch of 5 docs (same spec) to exercise incremental ingestion
- Generate a further batch of 10 docs (same spec) to exercise re-ranking as the corpus grows

## RAG — Read (ingestion)
- Decide: parsing/extraction approach for PDF/DOCX/HTML with tables, images, mixed layout, bilingual content — justify the choice
- Write the module that loads and parses docs
- Support incremental ingestion (add new docs without reprocessing the whole corpus)

## RAG — Store
- Decide: vector DB (must be local, must have an official Docker image) — justify the choice
- Decide: embedding model — justify the choice
- Decide: chunking strategy — justify the choice

## RAG — Generate
- Decide: LLM for retrieval/generation — justify the choice
- Integrate LLM via API, replacing the mocked responses
- Implement re-ranking (to demonstrate retrieval quality as the corpus grows, see corpus batches above)
- Implement prompt guardrails:
    - Protection against prompt injection
    - Clear system instructions and role separation
    - Constraints to keep responses aligned with the provided knowledge base

## Ops / Packaging
- `docker-compose.yml`: backend service + local vector DB service, no load balancer
- Docker image builds via `uv`, consistent with local dev
- Verify `docker compose up` gives a working app with no manual DB setup
- Package the whole project as a single zip for delivery

## Testing
- ~~Set up Playwright (`pytest-playwright`) e2e testing, with an accessible-role/text locator convention (`.claude/skills/e2e-testing/SKILL.md`)~~
- ~~e2e tests: page loads with expected elements; title/input stay pinned on long conversations; log scrolls to reveal latest reply~~
- Single-prompt latency tests asserting completion under 5s
- Lightweight concurrent-users test (a handful of simulated users) showing no unacceptable degradation
- Decide: how to demonstrate/measure answer accuracy and reliability (golden Q&A set + eval? reasoned design only?)

## Docs
- Architecture overview
- Key design decisions and trade-offs
- Chosen models, tools, and technologies
- ~~Track prompts used during development~~ (`scripts/export_chat_log.py`)
- Note the AI trace capture is Claude-Code-only, not a general multi-tool/multi-dev capture (known limitation, requirements §9)
