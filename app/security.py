"""Signed-token check on the API endpoints.

**This is not authentication.** There is no login and no user identity: anyone
who can load the chat page is handed a token. It stops casual direct calls to
the API and nothing more. What it does demonstrate is the mechanism real auth
would use — a signed, expiring credential, verified on every request, attached
in one place rather than re-implemented per endpoint. See
`docs/considerations.md`.
"""
import logging
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException, Request, status

from app.config import get_settings
from app.logging_config import APP_LOGGER

ALGORITHM = "HS256"

logger = logging.getLogger(APP_LOGGER)


def issue_token() -> str:
    """Mint a short-lived token to embed in the chat page."""
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {"iat": now, "exp": now + timedelta(seconds=settings.jwt_ttl_seconds)}
    return jwt.encode(
        payload, settings.jwt_secret.get_secret_value(), algorithm=ALGORITHM
    )


def _unauthorized(reason: str) -> HTTPException:
    # Reason is logged, not returned — the client gets a flat 401 either way.
    logger.warning("rejected API request reason=%s", reason)
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def verify_token(request: Request) -> None:
    """FastAPI dependency — attach to one endpoint with `Depends(verify_token)`,
    or to every endpoint on a router with `dependencies=[Depends(verify_token)]`.
    """
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise _unauthorized("missing or malformed Authorization header")

    try:
        jwt.decode(
            token,
            get_settings().jwt_secret.get_secret_value(),
            algorithms=[ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise _unauthorized("token expired") from None
    except jwt.InvalidTokenError:
        raise _unauthorized("invalid token") from None
