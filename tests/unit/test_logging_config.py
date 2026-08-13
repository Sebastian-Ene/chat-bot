import logging
from pathlib import Path

import pytest

from common.logging_config import (
    APP_LOGGER,
    INGEST_LOGGER,
    PERFORMANCE_LOGGER,
    configure_logging,
)

SERVICE = "api"


@pytest.fixture
def log_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reconfigure) -> Path:
    """Point logging at a temp dir, then restore real handlers afterwards.

    Yields the service's own directory, since that is where the files land.
    """
    monkeypatch.setenv("LOG_DIR", str(tmp_path))
    reconfigure()
    configure_logging(SERVICE)
    yield tmp_path / SERVICE
    for name in (APP_LOGGER, INGEST_LOGGER, PERFORMANCE_LOGGER):
        for handler in logging.getLogger(name).handlers:
            handler.close()
        logging.getLogger(name).handlers.clear()


def test_files_land_in_a_per_service_directory(log_dir: Path) -> None:
    """api and ingester share a LOG_DIR, so each must write its own subtree."""
    logging.getLogger(APP_LOGGER).info("ordinary log line")

    assert log_dir.name == SERVICE
    assert (log_dir / "app.log").exists()
    assert not (log_dir.parent / "app.log").exists(), "wrote to the shared root"


def test_app_and_performance_logs_go_to_separate_files(log_dir: Path) -> None:
    logging.getLogger(APP_LOGGER).info("ordinary log line")
    logging.getLogger(PERFORMANCE_LOGGER).debug("total_ms=1.23")

    app_log = (log_dir / "app.log").read_text()
    performance_log = (log_dir / "performance.log").read_text()

    assert "ordinary log line" in app_log
    assert "total_ms=1.23" in performance_log


def test_performance_records_do_not_leak_into_the_app_log(log_dir: Path) -> None:
    logging.getLogger(PERFORMANCE_LOGGER).debug("total_ms=1.23")

    # Handlers are created with delay=True, so a log nothing wrote to does not
    # exist at all — which satisfies this even more strongly than empty content.
    app_log = log_dir / "app.log"
    assert "total_ms" not in (app_log.read_text() if app_log.exists() else "")


def test_configure_logging_is_idempotent(log_dir: Path) -> None:
    before = len(logging.getLogger(APP_LOGGER).handlers)

    configure_logging(SERVICE)

    assert len(logging.getLogger(APP_LOGGER).handlers) == before
