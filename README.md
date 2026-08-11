# chat-bot

## Running

    cp .env.example .env      # then fill in ANTHROPIC_API_KEY and JWT_SECRET
    ./run.sh                  # RELOAD=1 to restart on code changes

## Tests

    uv run pytest             # unit + API
    uv run pytest -m e2e      # browser-driven (see docs/considerations.md for setup)

## Logs

- `logs/app.log` — application logs, also on the console. INFO by default; at
  `LOG_LEVEL=DEBUG` it also carries a per-stage trace of each request, keyed by
  the id returned in the `X-Request-ID` response header.
- `logs/performance.log` — one line per request with the per-stage latency
  breakdown.
