# chat-bot

## Running

    cp .env.example .env      # then fill in ANTHROPIC_API_KEY and JWT_SECRET

    docker compose up -d      # api on :8000, qdrant on :6333
    docker compose logs -f api
    docker compose down

The ingester runs alongside them but is not published to the host — it is
reachable only from inside the compose network. It reads `corpus/docs-initial`
read-only; copying `corpus/docs-later/*` in there is how incremental ingestion
gets demonstrated.

Or without Docker:

    ./run.sh                  # RELOAD=1 to restart on code changes

`./app` and `./logs` are bind-mounted into the api container, so code changes
reload and logs are readable on the host.

## Tests

    uv run pytest                            # unit + API + ingestion
    uv run pytest tests/ingest               # ingestion only
    uv run pytest -m e2e                     # browser-driven (setup: docs/considerations.md)
    uv run pytest -m 'not e2e and not ingest'

A command-line `-m` replaces the `not e2e` filter in `addopts`, so exclusions
have to be spelled out in full — otherwise the Playwright tests run in the same
process as the anyio ones and break its event-loop runner.

## Logs

One directory per service, since both containers share the `./logs` mount and
two processes rotating the same file race each other.

- `logs/api/app.log` — application logs, also on the console. INFO by default;
  at `LOG_LEVEL=DEBUG` it also carries a per-stage trace of each request, keyed
  by the id returned in the `X-Request-ID` response header.
- `logs/api/performance.log` — one line per request with the per-stage latency
  breakdown and token usage.
- `logs/ingest/ingest.log` — ingestion runs: documents discovered and the plan
  (new / changed / unchanged / deleted).
- `logs/ingest/app.log` — the ingester's own startup and framework logs.

The directories are tracked (the log files are not): the containers run as a
non-root user, and Docker creates a missing bind-mount source as root, so a
clone without them cannot start.
