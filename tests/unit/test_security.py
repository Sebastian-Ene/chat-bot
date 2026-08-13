from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException, Request

from api.core.constants import JWT_ALGORITHM
from api.core.security import issue_token, verify_token
from api.core.config import get_settings


def _request(headers: dict[str, str] | None = None) -> Request:
    raw = [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()]
    return Request({"type": "http", "method": "POST", "path": "/api/chat", "headers": raw})


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _encode(payload: dict, secret: str | None = None) -> str:
    secret = secret or get_settings().jwt_secret.get_secret_value()
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def test_issued_token_verifies() -> None:
    verify_token(_request(_bearer(issue_token())))


def test_issued_token_carries_issued_at_and_expiry() -> None:
    claims = jwt.decode(
        issue_token(), get_settings().jwt_secret.get_secret_value(), algorithms=[JWT_ALGORITHM]
    )

    assert claims["exp"] - claims["iat"] == get_settings().jwt_ttl_seconds


def test_expired_token_is_rejected() -> None:
    expired = datetime.now(UTC) - timedelta(seconds=1)
    token = _encode({"iat": expired - timedelta(seconds=300), "exp": expired})

    with pytest.raises(HTTPException) as error:
        verify_token(_request(_bearer(token)))

    assert error.value.status_code == 401


def test_token_signed_with_another_secret_is_rejected() -> None:
    now = datetime.now(UTC)
    token = _encode(
        {"iat": now, "exp": now + timedelta(seconds=300)},
        secret="a-different-secret-long-enough-for-hs256",
    )

    with pytest.raises(HTTPException) as error:
        verify_token(_request(_bearer(token)))

    assert error.value.status_code == 401


def test_tampered_token_is_rejected() -> None:
    token = issue_token()
    tampered = token[:-2] + ("aa" if not token.endswith("aa") else "bb")

    with pytest.raises(HTTPException) as error:
        verify_token(_request(_bearer(tampered)))

    assert error.value.status_code == 401


@pytest.mark.parametrize(
    "headers",
    [
        pytest.param({}, id="no header"),
        pytest.param({"Authorization": ""}, id="empty header"),
        pytest.param({"Authorization": "Bearer"}, id="scheme with no token"),
        pytest.param({"Authorization": "Bearer "}, id="empty token"),
        pytest.param({"Authorization": "Basic abc123"}, id="wrong scheme"),
    ],
)
def test_missing_or_malformed_header_is_rejected(headers: dict[str, str]) -> None:
    with pytest.raises(HTTPException) as error:
        verify_token(_request(headers))

    assert error.value.status_code == 401


def test_bearer_scheme_is_case_insensitive() -> None:
    verify_token(_request({"Authorization": f"bearer {issue_token()}"}))


def test_rejection_does_not_leak_the_reason_to_the_client() -> None:
    with pytest.raises(HTTPException) as error:
        verify_token(_request())

    assert error.value.detail == "invalid or expired token"
    assert error.value.headers["WWW-Authenticate"] == "Bearer"
