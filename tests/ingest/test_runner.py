"""The run itself: what gets parsed, what the report says, what the job exits with.

`parse_all` is stubbed throughout — the runner's job is deciding *what* to parse,
and real parsing is covered by `test_parse_documents.py`.
"""
from pathlib import Path

import pytest
from qdrant_client import QdrantClient

from app.rag.ingest import __main__ as cli
from app.rag.ingest.discovery import DiscoveredDocument
from app.rag.ingest.runner import run

pytestmark = pytest.mark.ingest


def document(doc_id: str, content_hash: str = "hash") -> DiscoveredDocument:
    return DiscoveredDocument(
        doc_id=doc_id,
        path=Path("/corpus") / doc_id,
        source_format="pdf",
        size_bytes=1,
        content_hash=content_hash,
    )


@pytest.fixture
def client() -> QdrantClient:
    """Empty in-memory store: every discovered document is `new`."""
    return QdrantClient(":memory:")


@pytest.fixture
def corpus(monkeypatch: pytest.MonkeyPatch) -> list[DiscoveredDocument]:
    documents = [document("a.pdf"), document("b.pdf")]
    monkeypatch.setattr("app.rag.ingest.runner.discover", lambda _root: documents)
    return documents


@pytest.fixture
def parsed(monkeypatch: pytest.MonkeyPatch) -> list[list[DiscoveredDocument]]:
    """Records each `parse_all` call so tests can assert on what was sent."""
    calls: list[list[DiscoveredDocument]] = []

    def fake_parse_all(documents):
        calls.append(list(documents))
        return list(documents), []

    monkeypatch.setattr("app.rag.ingest.runner.parse_all", fake_parse_all)
    return calls


class TestDryRun:
    def test_nothing_is_parsed(self, client, corpus, parsed) -> None:
        run(client, dry_run=True)

        assert parsed == []

    def test_the_store_is_left_untouched(self, client, corpus, parsed) -> None:
        """"Show me what would happen" must not create anything."""
        from app.config import get_settings

        run(client, dry_run=True)

        assert not client.collection_exists(get_settings().qdrant_collection)

    def test_the_plan_is_still_reported(self, client, corpus, parsed) -> None:
        """The point of a dry run: see the work without doing it."""
        report = run(client, dry_run=True)

        assert report.discovered == 2
        assert len(report.plan.new) == 2
        assert "nothing parsed" in report.summary()


class TestPlanDrivesTheRun:
    def test_only_planned_documents_are_parsed(
        self, client, corpus, parsed, monkeypatch
    ) -> None:
        """An unchanged document must not be re-parsed — that is the whole point
        of deriving state from the collection."""
        monkeypatch.setattr(
            "app.rag.ingest.runner.build_plan",
            lambda _client, discovered: _plan_with_unchanged(discovered),
        )

        run(client)

        assert [d.doc_id for d in parsed[0]] == ["a.pdf"]

    def test_force_parses_everything(self, client, corpus, parsed, monkeypatch) -> None:
        monkeypatch.setattr(
            "app.rag.ingest.runner.build_plan",
            lambda _client, discovered: _plan_with_unchanged(discovered),
        )

        run(client, force=True)

        assert [d.doc_id for d in parsed[0]] == ["a.pdf", "b.pdf"]


def _plan_with_unchanged(discovered):
    from app.rag.ingest.state import IngestPlan

    return IngestPlan(new=[discovered[0]], unchanged=[discovered[1]])


class TestReport:
    def test_counts_what_was_parsed(self, client, corpus, parsed) -> None:
        report = run(client)

        assert report.parsed == 2
        assert report.ok

    def test_failures_are_named_not_just_counted(
        self, client, corpus, monkeypatch
    ) -> None:
        """A count alone cannot be acted on; the summary has to say which file."""
        monkeypatch.setattr(
            "app.rag.ingest.runner.parse_all", lambda documents: ([], ["b.pdf"])
        )

        report = run(client)

        assert report.failed == ["b.pdf"]
        assert not report.ok
        assert "b.pdf" in report.summary()


class TestCli:
    def test_flags_default_to_off(self) -> None:
        args = cli.parse_args([])

        assert args.force is False
        assert args.dry_run is False

    def test_flags_are_parsed(self) -> None:
        args = cli.parse_args(["--force", "--dry-run"])

        assert args.force and args.dry_run

    def test_exit_code_is_zero_on_a_clean_run(self, monkeypatch, capsys) -> None:
        _stub_job(monkeypatch, failed=[])

        assert cli.main([]) == 0

    def test_exit_code_is_non_zero_when_a_document_failed(
        self, monkeypatch, capsys
    ) -> None:
        """A scheduled run must not report success over a partially indexed corpus."""
        _stub_job(monkeypatch, failed=["broken.pdf"])

        assert cli.main([]) == 1


def _stub_job(monkeypatch: pytest.MonkeyPatch, *, failed: list[str]) -> None:
    from app.rag.ingest.runner import RunReport

    monkeypatch.setattr(cli, "configure_logging", lambda _service: None)
    monkeypatch.setattr(cli.vector_store, "check_connection", lambda: None)
    monkeypatch.setattr(cli.vector_store, "get_client", lambda: None)
    monkeypatch.setattr(
        cli, "run", lambda _client, force, dry_run: RunReport(failed=failed)
    )
