Just a POC. Did not consider making the ai logging necessary work for another dev or other ai tools than Claude.

Known limitation: `scripts/export_chat_log.py` (+ `.githooks/pre-commit`) only
captures Claude Code sessions. It satisfies this PoC's own AI-usage
transparency requirement (requirements.md §9), but it is not a general
multi-tool/multi-dev trace capture — another dev, or a different AI
assistant, would need separate tooling.

Diagram:

Nginx/AWS load balancer ->((server docker): uvicorn -> fastapi app )-> ( (db docker) vector db)

Use uvicorn + fastapi for speed (async)

E2E testing (Playwright):

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