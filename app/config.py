from functools import lru_cache

from dotenv import load_dotenv
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# `.env` is loaded into the OS environment; values already present there win,
# so real deployments can configure the app without shipping a file.
load_dotenv()


class Settings(BaseSettings):
    """Application configuration, read from the OS environment.

    The single place model and service configuration lives — secrets are never
    hardcoded in source (requirements.md §6.3, §7.3).
    """

    model_config = SettingsConfigDict(extra="ignore")

    anthropic_api_key: SecretStr
    anthropic_model: str = "claude-haiku-4-5"
    qdrant_url: str = "http://localhost:6333"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings, built once on first use."""
    return Settings()
