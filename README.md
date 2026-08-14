# chat-bot

A RAG chat assistant over a mixed-format document corpus — PDF, DOCX and HTML,
English and German, with tables and charts that hold information found nowhere
in the surrounding text. Questions are answered from the indexed documents only,
and declined when the corpus does not cover them.

Docling parses, BGE-M3 embeds (dense + sparse from one pass), Qdrant searches
hybrid with RRF fusion, Claude Haiku 4.5 answers.

## Docs

Read in this order — each is a summary, and the depth sits behind it.

| | |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | deployment units, code layout, both pipelines |
| [`docs/design-decisions.md`](docs/design-decisions.md) | every decision with its trade-off, and the current measurements |
| [`docs/technologies.md`](docs/technologies.md) | models, versions, tooling |

Then, when a line above raises *why that way?*:

| | |
|---|---|
| [`docs/considerations.md`](docs/considerations.md) | the full reasoning, written as it happened and corrected in place. Its **Known issues** and **Improvements** sections read on their own — what is accepted as missing, and what broke and got fixed |
| [`docs/requirements.md`](docs/requirements.md) | what was specified |
| [`docs/work.md`](docs/work.md) | the run-list |

## Running

    cp .env.example .env      # then fill in ANTHROPIC_API_KEY and JWT_SECRET

    docker compose up -d      # api on :8000, qdrant on :6333
    docker compose logs -f api
    docker compose down

The chat UI is at `http://localhost:8000`. Interactive API docs come from
FastAPI at `/docs` (Swagger) and `/redoc` — `/api/chat` needs the page token, so
load `/`, copy the token out of the HTML and paste it into **Authorize**.

Or without Docker, providing your own Qdrant:

    ./run.sh                  # RELOAD=1 to restart on code changes

`./api`, `./common`, `./ingestion` and `./logs` are bind-mounted into the
containers, so code changes reload and logs are readable on the host.

## Ingestion

A job, not a service — it runs to completion and exits, so `docker compose up`
does not start it:

    docker compose run --rm ingest --dry-run   # what a run would do
    docker compose run --rm ingest             # ingest what changed
    docker compose run --rm ingest --force     # re-process everything

It reads `corpus/docs-initial` read-only, and takes no directory argument — the
root is the `CORPUS_DIR` setting. Copying `corpus/docs-later/*` in there and
running it again is how incremental ingestion gets demonstrated. Exit status is
non-zero if any document failed to parse.

20 documents produce 201 chunks; a full run takes minutes, nearly all of it
parsing.

## Evaluation

51 golden questions against a running stack, answers graded by an LLM judge:

    uv run python -m scripts.eval_golden                 # answer correctness
    uv run python -m scripts.eval_golden --retrieval     # + recall@k and MRR
    uv run python -m scripts.eval_golden --golden 1      # one set only

Reports land in `logs/common/golden_qa.{json,md}`. Exit status is non-zero if
any question failed. **It calls the Anthropic API** — roughly 200 calls for a
full run, including the Opus 5 judge.

Last run: answerable **42/42**, must-decline 5/9, recall@10 41/42, MRR 0.826,
latency p95 4.97 s. See `docs/design-decisions.md`.

## Tests

    uv run pytest                            # the fast suite
    uv run pytest tests/ingest               # ingestion only
    uv run pytest -m docling                 # real documents, real models — minutes
    uv run pytest -m embedding               # loads BGE-M3 for real
    uv run pytest -m e2e                     # browser-driven (setup: docs/considerations.md)

The default run excludes `e2e`, `docling` and `embedding`. A command-line `-m`
replaces that whole filter, so exclusions have to be spelled out in full —
otherwise the Playwright tests run in the same process as the anyio ones and
break its event-loop runner.

## Logs

One directory per service, since both containers share the `./logs` mount and
two processes rotating the same file race each other.

- `logs/api/app.log` — application logs, also on the console. INFO by default;
  at `LOG_LEVEL=DEBUG` it also carries a per-stage trace of each request, keyed
  by the id returned in the `X-Request-ID` response header.
- `logs/api/performance.log` — one line per request with the per-stage latency
  breakdown and token usage.
- `logs/ingest/ingest.log` — ingestion runs: the plan (new / changed /
  unchanged / deleted), one line per document parsed, and the run summary.
- `logs/ingest/app.log` — the ingest job's framework logs.
- `logs/common/` — evaluation reports and the figure-description cache.

The directories are tracked (the log files are not): the containers run as a
non-root user, and Docker creates a missing bind-mount source as root, so a
clone without them cannot start.
