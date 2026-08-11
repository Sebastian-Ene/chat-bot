import os
import socket
import threading

import pytest
import uvicorn

# Set before `app.config` loads `.env`, so tests never reach for a real key.
# `load_dotenv()` does not override values already in the environment.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
# At least 32 bytes — PyJWT warns below that for HS256 (RFC 7518 §3.2).
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-long-enough-for-hs256")

from app import vector_store  # noqa: E402

# Startup fails hard when Qdrant is unreachable, and the e2e `live_server`
# fixture runs the real lifespan. Stub it here so the suite stays hermetic — a
# page test should not need a database.
vector_store.check_connection = lambda: []

from app.main import app  # noqa: E402
from tests.fake_anthropic import FakeAnthropic  # noqa: E402


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """A valid token, as the chat page would embed."""
    from app.security import issue_token

    return {"Authorization": f"Bearer {issue_token()}"}


@pytest.fixture(autouse=True)
def stub_anthropic(monkeypatch: pytest.MonkeyPatch) -> FakeAnthropic:
    """No test may call the real API — including e2e, which drives the app
    in-process via `live_server`, so patching the module attribute reaches it."""
    client = FakeAnthropic()
    monkeypatch.setattr("app.anthropic_client.get_client", lambda: client)
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
