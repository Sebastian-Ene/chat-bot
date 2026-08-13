"""Logging setup: ordinary app logs and performance logs go to separate files.

Two loggers:

- `app` — ordinary application logs at INFO. Console *and* file, so
  `docker compose logs` stays useful while the file survives for analysis.
- `app.performance` — per-stage latency breakdowns at DEBUG. File only, with
  `propagate = False` so timing noise never reaches the general log.
"""
import logging
from logging.handlers import RotatingFileHandler

from common.config import get_settings
from common.request_context import RequestIdFilter

APP_LOGGER = "app"
PERFORMANCE_LOGGER = "app.performance"
INGEST_LOGGER = "app.ingest"

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
    # delay=True: the file appears on first write, so a service does not leave
    # empty files for logs it never emits — the api creates no ingest.log.
    handler = RotatingFileHandler(
        path, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, delay=True
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(_FORMAT))
    return handler


def configure_logging(service: str) -> None:
    """Set up logging for one service, writing under `LOG_DIR/<service>`.

    The service names itself rather than relying on configuration: api and
    ingester share the same `LOG_DIR`, and two processes rotating one file race
    each other. Passing it explicitly keeps the split true however the process
    is started — container, `run.sh`, or a test.

    Idempotent: repeated calls replace handlers rather than stacking them.
    """
    settings = get_settings()
    log_dir = settings.log_dir / service
    log_dir.mkdir(parents=True, exist_ok=True)
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
    app_logger.addHandler(_file_handler(log_dir / "app.log", level))

    # Ingestion writes its own file: it is a different workload, running in a
    # different container, and its story is a run rather than a request.
    ingest_logger = logging.getLogger(INGEST_LOGGER)
    ingest_logger.setLevel(level)
    ingest_logger.handlers.clear()
    ingest_logger.filters.clear()
    ingest_logger.addFilter(RequestIdFilter())
    ingest_logger.addHandler(console)  # so `docker compose logs ingester` shows it
    ingest_logger.addHandler(_file_handler(log_dir / "ingest.log", level))
    ingest_logger.propagate = False

    performance_logger = logging.getLogger(PERFORMANCE_LOGGER)
    performance_logger.setLevel(level)
    performance_logger.handlers.clear()
    performance_logger.filters.clear()
    performance_logger.addFilter(RequestIdFilter())
    performance_logger.addHandler(
        _file_handler(log_dir / "performance.log", level)
    )
    performance_logger.propagate = False
