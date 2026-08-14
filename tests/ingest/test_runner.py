"""The run: what gets processed, what a failure costs, what the report says.

Every stage is stubbed — the runner's job is deciding *what* to process and
what to do when one document goes wrong, not parsing or embedding.
"""
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest
from qdrant_client import QdrantClient

from common.logging_config import INGEST_LOGGER
from ingestion import __main__ as cli
from ingestion.discovery import DiscoveredDocument
from ingestion.runner import DocumentFailed, RunReport, ingest_document, run
from ingestion.state import IngestPlan

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
    monkeypatch.setattr("ingestion.runner.discover", lambda _root: documents)
    return documents


@pytest.fixture
def pipeline(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Stubs the whole per-document pipeline, recording what reached it."""
    processed: list[str] = []

    def fake_ingest_document(_client, document):
        processed.append(document.doc_id)
        return 3

    monkeypatch.setattr(
        "ingestion.runner.ingest_document", fake_ingest_document
    )
    monkeypatch.setattr("ingestion.runner.delete_documents", lambda *_args: 0)
    return processed


def plan_with_unchanged(discovered):
    return IngestPlan(new=[discovered[0]], unchanged=[discovered[1]])


class TestDryRun:
    def test_nothing_is_processed(self, client, corpus, pipeline) -> None:
        run(client, dry_run=True)

        assert pipeline == []

    def test_the_store_is_left_untouched(self, client, corpus, pipeline) -> None:
        """"Show me what would happen" must not create anything."""
        from common.config import get_settings

        run(client, dry_run=True)

        assert not client.collection_exists(get_settings().qdrant_collection)

    def test_the_plan_is_still_reported(self, client, corpus, pipeline) -> None:
        report = run(client, dry_run=True)

        assert report.discovered == 2
        assert len(report.plan.new) == 2
        assert "nothing written" in report.summary()


class TestPlanDrivesTheRun:
    def test_only_planned_documents_are_processed(
        self, client, corpus, pipeline, monkeypatch
    ) -> None:
        """An unchanged document must not be re-processed — that is the whole
        point of deriving state from the collection."""
        monkeypatch.setattr(
            "ingestion.runner.build_plan",
            lambda _client, discovered: plan_with_unchanged(discovered),
        )

        run(client)

        assert pipeline == ["a.pdf"]

    def test_force_processes_everything(
        self, client, corpus, pipeline, monkeypatch
    ) -> None:
        monkeypatch.setattr(
            "ingestion.runner.build_plan",
            lambda _client, discovered: plan_with_unchanged(discovered),
        )

        run(client, force=True)

        assert pipeline == ["a.pdf", "b.pdf"]


class TestFailureIsolation:
    @pytest.fixture
    def one_bad_document(self, monkeypatch: pytest.MonkeyPatch) -> list[str]:
        processed: list[str] = []

        def fake_ingest_document(_client, document):
            if document.doc_id == "a.pdf":
                raise DocumentFailed("a.pdf: embed: RuntimeError: out of memory")
            processed.append(document.doc_id)
            return 3

        monkeypatch.setattr(
            "ingestion.runner.ingest_document", fake_ingest_document
        )
        monkeypatch.setattr("ingestion.runner.delete_documents", lambda *_args: 0)
        return processed

    def test_the_rest_of_the_corpus_still_runs(
        self, client, corpus, one_bad_document
    ) -> None:
        run(client)

        assert one_bad_document == ["b.pdf"]

    def test_the_failure_is_named_in_the_report(
        self, client, corpus, one_bad_document
    ) -> None:
        """A count alone cannot be acted on; a retry starts from the doc_id."""
        report = run(client)

        assert report.failed == ["a.pdf"]
        assert report.indexed == 1
        assert not report.ok
        assert "a.pdf" in report.summary()

    def test_the_error_log_names_the_stage(
        self, client, corpus, one_bad_document, caplog
    ) -> None:
        """Production alerts on these; "which document, which stage" is what a
        fix or a retry starts from."""
        with caplog.at_level(logging.ERROR, logger=INGEST_LOGGER):
            run(client)

        assert "a.pdf" in caplog.text
        assert "embed" in caplog.text


class TestDeletions:
    def test_removed_documents_have_their_points_deleted(
        self, client, corpus, monkeypatch
    ) -> None:
        deleted = []
        monkeypatch.setattr(
            "ingestion.runner.ingest_document", lambda _client, _doc: 1
        )
        monkeypatch.setattr(
            "ingestion.runner.delete_documents",
            lambda _client, doc_ids: deleted.append(doc_ids) or 7,
        )
        monkeypatch.setattr(
            "ingestion.runner.build_plan",
            lambda _client, discovered: IngestPlan(
                new=list(discovered), deleted=["gone.pdf"]
            ),
        )

        report = run(client)

        assert deleted == [["gone.pdf"]]
        assert report.points_deleted == 7


class TestIngestDocument:
    def test_names_the_stage_that_failed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without the stage, an error says a document is broken but not where
        to look."""
        monkeypatch.setattr(
            "ingestion.runner.parse",
            lambda _document: (_ for _ in ()).throw(RuntimeError("boom")),
        )

        with pytest.raises(DocumentFailed, match="parse"):
            ingest_document(None, document("a.pdf"))

    def test_a_document_with_no_chunks_is_not_a_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Some documents legitimately hold nothing chunkable."""
        # `.document.pictures` is what the describe stage reads; empty means it
        # returns without reaching settings or the network.
        parsed = SimpleNamespace(document=SimpleNamespace(pictures=[]))
        monkeypatch.setattr("ingestion.runner.parse", lambda _document: parsed)
        monkeypatch.setattr("ingestion.runner.chunk", lambda _parsed: [])

        assert ingest_document(None, document("empty.pdf")) == 0


class TestCli:
    def test_flags_default_to_off(self) -> None:
        args = cli.parse_args([])

        assert args.force is False
        assert args.dry_run is False

    def test_flags_are_parsed(self) -> None:
        args = cli.parse_args(["--force", "--dry-run"])

        assert args.force and args.dry_run

    def test_exit_code_is_zero_on_a_clean_run(self, monkeypatch) -> None:
        _stub_job(monkeypatch, failed=[])

        assert cli.main([]) == 0

    def test_exit_code_is_non_zero_when_a_document_failed(self, monkeypatch) -> None:
        """A scheduled run must not report success over a partially indexed
        corpus."""
        _stub_job(monkeypatch, failed=["broken.pdf"])

        assert cli.main([]) == 1


def _stub_job(monkeypatch: pytest.MonkeyPatch, *, failed: list[str]) -> None:
    monkeypatch.setattr(cli, "configure_logging", lambda _service: None)
    monkeypatch.setattr(cli.vector_store, "check_connection", lambda: None)
    monkeypatch.setattr(cli.vector_store, "get_client", lambda: None)
    monkeypatch.setattr(
        cli, "run", lambda _client, force, dry_run: RunReport(failed=failed)
    )
