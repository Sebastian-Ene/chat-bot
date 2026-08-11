"""Logging setup: ordinary app logs and performance logs go to separate files.

Two loggers:

- `app` — ordinary application logs at INFO. Console *and* file, so
  `docker compose logs` stays useful while the file survives for analysis.
- `app.performance` — per-stage latency breakdowns at DEBUG. File only, with
  `propagate = False` so timing noise never reaches the general log.
"""
import logging
from logging.handlers import RotatingFileHandler

from app.config import get_settings
from app.request_context import RequestIdFilter

APP_LOGGER = "app"
PERFORMANCE_LOGGER = "app.performance"

_FORMAT = "%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s"
_MAX_BYTES = 5 * 1024 * 1024
_BACKUP_COUNT = 3


def truncate(text: str) -> str:
    """Cap text in trace lines, marking what was dropped."""
    limit = get_settings().log_max_chars
    if len(text) <= limit:
        return text
    return f"{text[:limit]}…(+{len(text) - limit} more chars)"


def _file_handler(path, level: int) -> RotatingFileHandler:
    handler = RotatingFileHandler(path, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_FORMAT))
    return handler


def configure_logging() -> None:
    """Idempotent — repeated calls replace handlers rather than stacking them."""
    settings = get_settings()
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    level = logging.getLevelNamesMapping()[settings.log_level.upper()]

    app_logger = logging.getLogger(APP_LOGGER)
    app_logger.setLevel(level)
    app_logger.handlers.clear()
    app_logger.filters.clear()
    app_logger.addFilter(RequestIdFilter())

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(_FORMAT))
    app_logger.addHandler(console)
    app_logger.addHandler(_file_handler(settings.log_dir / "app.log", level))

    performance_logger = logging.getLogger(PERFORMANCE_LOGGER)
    performance_logger.setLevel(level)
    performance_logger.handlers.clear()
    performance_logger.filters.clear()
    performance_logger.addFilter(RequestIdFilter())
    performance_logger.addHandler(
        _file_handler(settings.log_dir / "performance.log", level)
    )
    performance_logger.propagate = False
