import re

from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

from api.core.security import verify_token
from api.main import app

client = TestClient(app)

TOKEN_META = re.compile(r'<meta name="chat-token" content="([^"]+)"')


def test_page_embeds_a_usable_token() -> None:
    response = client.get("/")

    assert response.status_code == 200
    match = TOKEN_META.search(response.text)
    assert match, "chat page did not embed a token"
    # What `bearer_scheme` would hand the dependency for this token.
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=match.group(1)
    )
    verify_token(credentials)  # raises if the token is not valid


def test_page_itself_needs_no_token() -> None:
    """The page is how a client obtains a token, so it cannot require one."""
    assert client.get("/").status_code == 200
