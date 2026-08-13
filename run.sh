#!/usr/bin/env bash
# Run the app locally. Needs a .env with ANTHROPIC_API_KEY (see .env.example).
# Set RELOAD=1 to restart on code changes.
# set -euo pipefail

# cd "$(dirname "$0")"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

args=(uv run uvicorn api.main:app --host "$HOST" --port "$PORT")
[ "${RELOAD:-0}" = "1" ] && args+=(--reload)

exec "${args[@]}"
