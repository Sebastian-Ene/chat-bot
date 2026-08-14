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
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.core.constants import JWT_ALGORITHM
from api.core.config import get_settings
from common.logging_config import APP_LOGGER

logger = logging.getLogger(APP_LOGGER)

# Declared as a security scheme rather than read off the raw request, so it
# reaches the OpenAPI schema and `/docs` grows an Authorize button. `auto_error`
# is off because the scheme's own rejection is a bare 403 — this module raises
# its own 401 with `WWW-Authenticate`, and logs why.
bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="PageToken",
    description=(
        "Short-lived HS256 token embedded in the chat page. Load `/` and copy "
        "the token out of the HTML to try an endpoint here. Not authentication: "
        "anyone who can load the page gets one."
    ),
)


def issue_token() -> str:
    """Mint a short-lived token to embed in the chat page."""
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {"iat": now, "exp": now + timedelta(seconds=settings.jwt_ttl_seconds)}
    return jwt.encode(
        payload, settings.jwt_secret.get_secret_value(), algorithm=JWT_ALGORITHM
    )


def _unauthorized(reason: str) -> HTTPException:
    # Reason is logged, not returned — the client gets a flat 401 either way.
    logger.warning("rejected API request reason=%s", reason)
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    """FastAPI dependency — attach to one endpoint with `Depends(verify_token)`,
    or to every endpoint on a router with `dependencies=[Depends(verify_token)]`.
    """
    if credentials is None or not credentials.credentials:
        raise _unauthorized("missing or malformed Authorization header")

    try:
        jwt.decode(
            credentials.credentials,
            get_settings().jwt_secret.get_secret_value(),
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise _unauthorized("token expired") from None
    except jwt.InvalidTokenError:
        raise _unauthorized("invalid token") from None
