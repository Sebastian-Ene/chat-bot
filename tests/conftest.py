import os
import socket
import threading

import pytest
import uvicorn

# Set before `common.config` loads `.env`, so tests never reach for a real key.
# `load_dotenv()` does not override values already in the environment.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
# At least 32 bytes — PyJWT warns below that for HS256 (RFC 7518 §3.2).
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-long-enough-for-hs256")
# Required with no default. Nothing in the default suite reaches a real Qdrant —
# the tests that do build their own in-memory client.
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")

from common import vector_store  # noqa: E402

# Startup fails hard when Qdrant is unreachable, and the e2e `live_server`
# fixture runs the real lifespan. Stub it here so the suite stays hermetic — a
# page test should not need a database.
vector_store.check_connection = lambda: []

from api.core.config import ApiSettings  # noqa: E402
from api.main import app  # noqa: E402
from common.config import configure  # noqa: E402
from tests.fake_anthropic import FakeAnthropic  # noqa: E402

# At import, not only per test: fixtures scoped above `function` are set up
# before the autouse fixture below runs, so without this they would read
# configuration that nothing had injected yet.
configure(ApiSettings())


@pytest.fixture(autouse=True)
def settings():
    """`common/` owns no settings — an entrypoint injects them.

    `TestClient(app)` does not run the lifespan, so without this nothing would
    configure them and every read would raise `ConfigNotSet`. Tests that change
    the environment mid-case call `reconfigure()` to rebuild from it.

    Injects on setup and deliberately does *not* reset on teardown: fixtures
    scoped above `function` are set up between tests, and a torn-down slot
    would leave them reading unconfigured settings.
    """
    from common.config import configure

    return configure(ApiSettings())


@pytest.fixture
def reconfigure():
    """Rebuild the settings from the current environment.

    Replaces the old `get_settings.cache_clear()`: there is no cache to drop
    any more, so a test that sets an env var re-injects instead.
    """
    from api.core.config import ApiSettings
    from common.config import configure

    return lambda: configure(ApiSettings())


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """A valid token, as the chat page would embed."""
    from api.core.security import issue_token

    return {"Authorization": f"Bearer {issue_token()}"}


@pytest.fixture(autouse=True)
def stub_anthropic(monkeypatch: pytest.MonkeyPatch) -> FakeAnthropic:
    """No test may call the real API — including e2e, which drives the app
    in-process via `live_server`, so patching the module attribute reaches it."""
    client = FakeAnthropic()
    monkeypatch.setattr("api.rag.anthropic_client.get_client", lambda: client)
    return client


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def live_server() -> str:
    """Run the FastAPI app on a real port so browser-driven e2e tests can hit it."""
    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        pass

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=5)
