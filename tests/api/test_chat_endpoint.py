from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_returns_streamed_reply() -> None:
    response = client.post("/api/chat", json={"message": "hello there"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text.strip() == "This is a mocked response from the LLM."


def test_chat_rejects_missing_message() -> None:
    response = client.post("/api/chat", json={})

    assert response.status_code == 422


def test_chat_rejects_empty_message() -> None:
    response = client.post("/api/chat", json={"message": ""})

    assert response.status_code == 422


def test_chat_rejects_blank_message() -> None:
    response = client.post("/api/chat", json={"message": "     "})

    assert response.status_code == 422


def test_chat_rejects_message_below_min_length() -> None:
    response = client.post("/api/chat", json={"message": "hi"})

    assert response.status_code == 422


def test_chat_rejects_message_above_max_length() -> None:
    response = client.post("/api/chat", json={"message": "x" * 301})

    assert response.status_code == 422


def test_chat_accepts_message_at_max_length() -> None:
    response = client.post("/api/chat", json={"message": "x" * 300})

    assert response.status_code == 200
