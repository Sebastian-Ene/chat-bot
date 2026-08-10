import re

from fastapi.testclient import TestClient

from app.main import app
from app.security import verify_token

client = TestClient(app)

TOKEN_META = re.compile(r'<meta name="chat-token" content="([^"]+)"')


def _request_with(token: str):
    from fastapi import Request

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/chat",
            "headers": [(b"authorization", f"Bearer {token}".encode())],
        }
    )


def test_page_embeds_a_usable_token() -> None:
    response = client.get("/")

    assert response.status_code == 200
    match = TOKEN_META.search(response.text)
    assert match, "chat page did not embed a token"
    verify_token(_request_with(match.group(1)))  # raises if the token is not valid


def test_page_itself_needs_no_token() -> None:
    """The page is how a client obtains a token, so it cannot require one."""
    assert client.get("/").status_code == 200
