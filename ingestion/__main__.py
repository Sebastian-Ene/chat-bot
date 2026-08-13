"""`python -m ingestion` — the ingestion job's entry point.

Argument handling and exit codes only; the pipeline lives in `runner.py`. The
corpus root is never an argument: it is the `CORPUS_DIR` setting, fixed at
startup, so a run cannot be aimed at arbitrary files on the host.
"""
import argparse
import sys

from common import vector_store
from common.config import configure
from common.logging_config import configure_logging
from ingestion.config import IngestSettings
from ingestion.runner import run


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m ingestion",
        description="Ingest the corpus directory into the vector store.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-process every document, ignoring the plan (use when the pipeline changed)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what the run would do and stop before parsing",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    # First, and before anything reads configuration: `common/` has no settings
    # of its own and serves whichever child the entrypoint injects.
    configure(IngestSettings())
    configure_logging("ingest")

    # Same fail-fast contract as the api: no vector store, no run.
    vector_store.check_connection()
    report = run(vector_store.get_client(), force=args.force, dry_run=args.dry_run)

    print(report.summary())
    # Non-zero when any document failed to parse, so a scheduled run surfaces it
    # instead of reporting success over a partially indexed corpus.
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
