"""The liveness probe.

The container HEALTHCHECK is this route's only consumer, so a break here fails
the container rather than a request — worth pinning down.
"""
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_reports_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_needs_no_token() -> None:
    """A probe that had to mint or carry a credential would be checking the
    wrong thing — and the HEALTHCHECK has no way to obtain one."""
    assert "authorization" not in {key.lower() for key in client.headers}
    assert client.get("/health").status_code == 200
