"""Finding documents to ingest, and identifying them by content.

The corpus is a tree, not a flat directory (`corpus/docs-initial/{coverage,bulk}/`),
so discovery recurses. Ordering is stable so two runs over an unchanged corpus
produce the same sequence — which makes logs and dry runs comparable.
"""
import hashlib
import logging
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from common.logging_config import INGEST_LOGGER

logger = logging.getLogger(INGEST_LOGGER)

DOCUMENT_SUFFIXES = {".pdf", ".docx", ".html"}
_HASH_CHUNK_BYTES = 1024 * 1024


@dataclass(frozen=True)
class DiscoveredDocument:
    """A document on disk, identified by where it is and what it contains."""

    doc_id: str  # POSIX path relative to the corpus root
    path: Path
    source_format: str  # pdf | docx | html
    size_bytes: int
    content_hash: str  # SHA-256 of the file's bytes

    @property
    def short_hash(self) -> str:
        return self.content_hash[:12]


def hash_file(path: Path) -> str:
    """Streamed, so a 25-page PDF does not have to fit in memory twice."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_HASH_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def _is_hidden(path: Path, root: Path) -> bool:
    """Dotfiles and anything inside a dot-directory, relative to the root."""
    return any(part.startswith(".") for part in path.relative_to(root).parts)


def discover(root: Path) -> list[DiscoveredDocument]:
    """Every ingestible document under `root`, at any depth, sorted by `doc_id`."""
    root = root.resolve()
    if not root.is_dir():
        return []

    documents = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in DOCUMENT_SUFFIXES or _is_hidden(path, root):
            continue
        documents.append(
            DiscoveredDocument(
                doc_id=path.relative_to(root).as_posix(),
                path=path,
                source_format=suffix.lstrip("."),
                size_bytes=path.stat().st_size,
                content_hash=hash_file(path),
            )
        )

    documents = sorted(documents, key=lambda document: document.doc_id)

    by_format = Counter(document.source_format for document in documents)
    logger.info(
        "discovered %d documents root=%s formats=%s bytes=%d",
        len(documents),
        root,
        dict(sorted(by_format.items())) or "none",
        sum(document.size_bytes for document in documents),
    )
    for document in documents:
        logger.debug(
            "discovered %s format=%s hash=%s bytes=%d",
            document.doc_id,
            document.source_format,
            document.short_hash,
            document.size_bytes,
        )
    return documents
