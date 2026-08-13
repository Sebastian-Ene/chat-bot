import hashlib
from pathlib import Path

import pytest

from ingestion.discovery import discover, hash_file

pytestmark = pytest.mark.ingest


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    """A tree, not a flat directory — the real corpus nests two levels."""
    (tmp_path / "coverage").mkdir()
    (tmp_path / "bulk" / "deeper").mkdir(parents=True)
    (tmp_path / ".hidden").mkdir()

    (tmp_path / "coverage" / "guide.pdf").write_bytes(b"pdf bytes")
    (tmp_path / "coverage" / "policy.docx").write_bytes(b"docx bytes")
    (tmp_path / "bulk" / "faq.html").write_bytes(b"html bytes")
    (tmp_path / "bulk" / "deeper" / "notes.pdf").write_bytes(b"deep bytes")

    # None of these should be picked up.
    (tmp_path / "bulk" / "README.md").write_bytes(b"not a document")
    (tmp_path / "bulk" / "golden_qa.json").write_bytes(b"the answer key")
    (tmp_path / ".hidden" / "secret.pdf").write_bytes(b"hidden")
    (tmp_path / "coverage" / ".draft.pdf").write_bytes(b"dotfile")
    return tmp_path


def test_finds_documents_at_any_depth(corpus: Path) -> None:
    assert [document.doc_id for document in discover(corpus)] == [
        "bulk/deeper/notes.pdf",
        "bulk/faq.html",
        "coverage/guide.pdf",
        "coverage/policy.docx",
    ]


def test_ignores_non_document_suffixes(corpus: Path) -> None:
    found = {document.doc_id for document in discover(corpus)}

    assert "bulk/README.md" not in found
    assert "bulk/golden_qa.json" not in found, "the answer key must never be ingested"


def test_ignores_dotfiles_and_dot_directories(corpus: Path) -> None:
    found = {document.doc_id for document in discover(corpus)}

    assert not any(part.startswith(".") for doc_id in found for part in doc_id.split("/"))


def test_ordering_is_stable(corpus: Path) -> None:
    assert [d.doc_id for d in discover(corpus)] == [d.doc_id for d in discover(corpus)]


def test_records_format_and_size(corpus: Path) -> None:
    by_id = {document.doc_id: document for document in discover(corpus)}

    assert by_id["coverage/guide.pdf"].source_format == "pdf"
    assert by_id["coverage/policy.docx"].source_format == "docx"
    assert by_id["bulk/faq.html"].source_format == "html"
    assert by_id["coverage/guide.pdf"].size_bytes == len(b"pdf bytes")


def test_missing_root_yields_nothing(tmp_path: Path) -> None:
    assert discover(tmp_path / "nope") == []


class TestHashing:
    def test_matches_sha256_of_the_bytes(self, tmp_path: Path) -> None:
        path = tmp_path / "a.pdf"
        path.write_bytes(b"some content")

        assert hash_file(path) == hashlib.sha256(b"some content").hexdigest()

    def test_changes_when_content_changes(self, tmp_path: Path) -> None:
        path = tmp_path / "a.pdf"
        path.write_bytes(b"before")
        before = hash_file(path)
        path.write_bytes(b"after")

        assert hash_file(path) != before

    def test_identical_content_in_different_files_hashes_alike(self, tmp_path: Path) -> None:
        (tmp_path / "one.pdf").write_bytes(b"same")
        (tmp_path / "two.pdf").write_bytes(b"same")

        assert hash_file(tmp_path / "one.pdf") == hash_file(tmp_path / "two.pdf")
