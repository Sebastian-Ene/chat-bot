import logging
from pathlib import Path

import pytest

from app.config import get_settings
from app.logging_config import APP_LOGGER, PERFORMANCE_LOGGER, configure_logging


@pytest.fixture
def log_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point logging at a temp dir, then restore real handlers afterwards."""
    monkeypatch.setenv("LOG_DIR", str(tmp_path))
    get_settings.cache_clear()
    configure_logging()
    yield tmp_path
    for name in (APP_LOGGER, PERFORMANCE_LOGGER):
        for handler in logging.getLogger(name).handlers:
            handler.close()
        logging.getLogger(name).handlers.clear()
    get_settings.cache_clear()


def test_app_and_performance_logs_go_to_separate_files(log_dir: Path) -> None:
    logging.getLogger(APP_LOGGER).info("ordinary log line")
    logging.getLogger(PERFORMANCE_LOGGER).debug("total_ms=1.23")

    app_log = (log_dir / "app.log").read_text()
    performance_log = (log_dir / "performance.log").read_text()

    assert "ordinary log line" in app_log
    assert "total_ms=1.23" in performance_log


def test_performance_records_do_not_leak_into_the_app_log(log_dir: Path) -> None:
    logging.getLogger(PERFORMANCE_LOGGER).debug("total_ms=1.23")

    assert "total_ms" not in (log_dir / "app.log").read_text()


def test_configure_logging_is_idempotent(log_dir: Path) -> None:
    before = len(logging.getLogger(APP_LOGGER).handlers)

    configure_logging()

    assert len(logging.getLogger(APP_LOGGER).handlers) == before
