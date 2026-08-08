import socket
import threading

import pytest
import uvicorn

from app.main import app


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
