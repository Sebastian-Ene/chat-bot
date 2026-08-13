"""Settings the api needs on top of the shared ones.

The ingest job never reads any of these — which is the point of the split: it
should not have to supply an Anthropic key or a JWT secret to run.
"""
from pydantic import SecretStr

from common import config
from common.config import Settings


class ApiSettings(Settings):
    anthropic_api_key: SecretStr
    anthropic_model: str = "claude-haiku-4-5"

    # One secret for the whole app, supplied via `.env`. Every process that
    # serves the app must share it, or tokens minted by one are rejected by
    # another.
    jwt_secret: SecretStr
    jwt_ttl_seconds: int = 1800

    # Per-branch candidates before fusion, and how many survive it. Prefetch is
    # deliberately wider than top_k: RRF can only rank what the branches
    # surfaced, so a chunk missing from every branch's shortlist is unreachable.
    retrieval_prefetch_limit: int = 20
    retrieval_top_k: int = 5

    # Extra retrieval branches from the rewrite. Both are unproven — switch them
    # off to A/B against the eval harness once a corpus exists.
    rewrite_keywords_enabled: bool = True
    rewrite_sub_queries_enabled: bool = True


def get_settings() -> ApiSettings:
    """The injected settings, narrowed to the api's type.

    Same single instance `common.config.get_settings()` returns — this only
    tells the reader (and the type checker) which subclass it is.
    """
    settings = config.get_settings()
    if not isinstance(settings, ApiSettings):
        raise config.ConfigNotSet(
            f"the api needs ApiSettings, but {type(settings).__name__} was configured"
        )
    return settings
