"""One Anthropic client for the whole app.

Both pipeline stages that call the API (query analysis, generation) share it, so
there is a single connection pool — and a single place for tests to stub.
"""
from functools import lru_cache

import anthropic

from app.config import get_settings


@lru_cache
def get_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(
        api_key=get_settings().anthropic_api_key.get_secret_value()
    )
