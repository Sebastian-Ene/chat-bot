import os
import socket
import threading

import pytest
import uvicorn

# Set before `app.config` loads `.env`, so tests never reach for a real key.
# `load_dotenv()` does not override values already in the environment.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from app.main import app  # noqa: E402
from tests.fake_anthropic import FakeAnthropic  # noqa: E402


@pytest.fixture(autouse=True)
def stub_anthropic(monkeypatch: pytest.MonkeyPatch) -> FakeAnthropic:
    """No test may call the real API — including e2e, which drives the app
    in-process via `live_server`, so patching the module attribute reaches it."""
    client = FakeAnthropic()
    monkeypatch.setattr("app.rag.llm._client", lambda: client)
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
