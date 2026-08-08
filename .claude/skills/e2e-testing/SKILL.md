---
name: e2e-testing
description: Conventions for writing and running this project's Playwright e2e tests (browser-driven, against the real FastAPI app). Use when adding or modifying anything in tests/e2e/.
---

# E2E testing conventions

This project uses Playwright (via `pytest-playwright`) to drive the real chat UI in a real browser against the real FastAPI app — not the in-process `TestClient`, since Playwright needs an actual HTTP server to open pages against.

## Locator rule: accessible roles/names and visible text only

**Never select elements by `id` or CSS class in a test** (`page.locator("#foo")`,
`page.locator(".bar")`).

Instead, use:
- `page.get_by_role(role, name=...)` — the primary tool. Match against how a
  screen reader / accessibility tree would describe the element.
- `page.get_by_text(text, exact=True)` — for content assertions.

To make this possible, interactive elements in the app must expose a stable
accessible name, independent of decorative copy (placeholders, styling
hooks) that's more likely to change:
- Inputs: an explicit `aria-label` (e.g. `aria-label="Chat message"`), not
  just a `placeholder` — placeholders are readable as accessible names as a
  fallback, but that's fragile if UX copy changes.
- Buttons: their visible text is usually a fine accessible name already
  (e.g. `<button>Send</button>` → `get_by_role("button", name="Send")`).
- Containers that matter to a test (e.g. the message log) should get a
  semantic `role` (`role="log"` for the chat conversation) plus
  `aria-label`, so tests can target them without a class/id.


## Running the suite

```bash
uv run playwright install chromium   # one-time; --with-deps needs interactive sudo, skip it here
uv run pytest tests/e2e
```

`tests/conftest.py` provides a session-scoped `live_server` fixture that runs
`app.main:app` via `uvicorn` in a background thread on a free local port and
yields the base URL — use it in any e2e test that needs a running server.

## File location

E2E tests live under `tests/e2e/`. Keep them separate from any future unit/integration tests (e.g. `tests/unit/`) so they can be run/skipped independently — they're slower and need a browser.