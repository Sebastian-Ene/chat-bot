# Models, tools and technologies

Versions are what the lockfile currently resolves. Why each was chosen is in
`docs/design-decisions.md`.

## Models

| Role | Model | Where it runs |
|---|---|---|
| Embeddings | **BGE-M3** (`BAAI/bge-m3`) — dense + sparse from one forward pass, multilingual, 8k input | Local, baked into both images |
| Generation | **Claude Haiku 4.5** (`claude-haiku-4-5`) | Anthropic API |
| Query analysis | **Claude Haiku 4.5**, structured output | Anthropic API |
| Figure description | **Claude Haiku 4.5** vision, via the OpenAI-compatible endpoint Docling's API describer speaks | Anthropic API |
| Eval judge | **Claude Opus 5** (`claude-opus-5`) | Anthropic API, eval only |

Alternatives weighed: `multilingual-e5-small/large` and Cohere embeddings;
Weaviate and Chroma for the store; Sonnet 5 / Opus 5 as the generation upgrade
path.

## Runtime

| Layer | Choice | Version |
|---|---|---|
| Language | Python | 3.14 |
| Web framework | FastAPI + uvicorn (async) | 0.141.1 / 0.52.1 |
| Frontend | Jinja2 templates, plain HTML + vanilla JS, no build step | 3.1.6 |
| Vector DB | Qdrant (server + `qdrant-client`, kept in step) | 1.19.0 |
| Embeddings runtime | `FlagEmbedding` on torch | 1.4.0 / 2.13.0 |
| LLM SDK | `anthropic` | 0.121.0 |
| Parsing | Docling / `docling-core` | 2.119.0 / 2.91.0 |
| Config | pydantic + pydantic-settings | 2.13.4 / 2.15.0 |
| Auth token | PyJWT (HS256) | 2.13.0 |
| Async | anyio | 4.14.2 |

## Tooling

| Purpose | Tool |
|---|---|
| Dependencies + venv | `uv`, `uv.lock`, dependency groups (`ingest`, `dev`) |
| Packaging | Docker, multi-stage, non-root; `docker-compose` for the stack |
| Tests | pytest, `pytest-playwright` (e2e), httpx |
| Eval | `scripts/eval_golden.py` — answer correctness + retrieval metrics |
| Corpus | `scripts/generate_corpus.py` — byte-identical regeneration |

Markers keep the slow paths out of the default run: `docling` (real parsing),
`embedding` (real BGE-M3), `ingest`, `e2e`.

Not set up: ruff, mypy, pre-commit, CI, coverage — see `docs/considerations.md`
→ Known issues #9.

## Commands

Interactive API docs come from FastAPI itself — `/docs` (Swagger UI), `/redoc`,
`/openapi.json`. The page token is declared as a security scheme, so `/docs` has
an **Authorize** button: load `/`, copy the token out of the HTML, paste it in.
Both need internet — the UI assets load from a CDN.

```bash
docker compose up                      # api + qdrant
docker compose run --rm ingest         # ingest what changed
docker compose run --rm ingest --force # re-process everything
uv run pytest -q                       # fast suite
uv run pytest -m docling               # real documents
uv run python -m scripts.eval_golden   # golden Q&A, needs the stack up
```
