"""Ingestion tests.

These cover the ingester, which runs in its own container and is the only part
of the system that touches Docling. Nothing here loads a model: discovery and
state are pure filesystem and Qdrant work, so they stay in the default run.

The Docling-backed tests will need excluding once they exist — they load layout
and table models and take minutes.
"""
import pytest

from common.config import configure
from ingestion.config import IngestSettings

# At import, for the same reason as the root conftest — and every
# module-scoped fixture in the suite lives in this directory, so these are
# exactly the ones that would otherwise read configuration too early.
configure(IngestSettings())


@pytest.fixture(autouse=True)
def settings():
    """Override the root fixture: this half of the suite is the ingest job, so
    it injects `IngestSettings` — `corpus_dir` and `chunk_max_tokens` do not
    exist on the api's.

    No teardown reset, for the same reason as the root fixture: every
    module-scoped fixture in the suite is in this directory.
    """
    from common.config import configure

    return configure(IngestSettings())


@pytest.fixture
def reconfigure():
    """Rebuild `IngestSettings` from the current environment."""
    from common.config import configure
    from ingestion.config import IngestSettings

    return lambda: configure(IngestSettings())
