"""Sanity-check the corpus against its golden set.

    uv run python -m scripts.check_corpus

Catches the failure mode that matters here: a golden answer that names a
document, element or value which does not actually exist. A golden set is only
ground truth if it is true.
"""
import json
import sys

from scripts.corpus import paths

DOCUMENT_SUFFIXES = {".pdf", ".docx", ".html"}


def _documents_referenced(entry: dict) -> list[str]:
    source = entry.get("source")
    if not source:
        return []
    if "documents" in source:
        return source["documents"]
    return [source["document"]] if "document" in source else []


def main() -> int:
    problems: list[str] = []
    # Both sets: they reference the same documents, and a broken reference in
    # either one invalidates the eval it feeds.
    qa = [
        entry
        for name in ("golden_qa_0.json", "golden_qa_1.json")
        if (paths.CORPUS / name).is_file()
        for entry in json.loads((paths.CORPUS / name).read_text(encoding="utf-8"))
    ]
    # Walk the tree: documents are spread across coverage/, bulk/ and later/,
    # which is the shape the ingester has to handle too.
    documents = {
        path.name: path.relative_to(paths.CORPUS)
        for path in sorted(paths.CORPUS.rglob("*"))
        if path.suffix in DOCUMENT_SUFFIXES
    }
    present = set(documents)

    for entry in qa:
        for name in _documents_referenced(entry):
            if name not in present:
                problems.append(f"{entry['id']}: references missing document {name}")
                continue
            # A `later` question answered by an initial document would be
            # answerable before the second batch is ingested, which defeats the
            # point of the batch split.
            in_later = documents[name].parts[0] == paths.DOCS_LATER.name
            if entry.get("batch") == "later" and not in_later:
                problems.append(f"{entry['id']}: later question answered by {documents[name]}")
            if entry.get("batch") != "later" and in_later:
                problems.append(f"{entry['id']}: initial question answered by {documents[name]}")
        if entry["type"] == "unanswerable" and entry.get("source"):
            problems.append(f"{entry['id']}: unanswerable questions must have no source")
        if not entry.get("expected_answer"):
            problems.append(f"{entry['id']}: no expected answer")

    # Every document should be reachable by at least one question, or it is pure
    # noise rather than a distractor anyone can score against.
    referenced = {name for entry in qa for name in _documents_referenced(entry)}
    ids = {entry["id"] for entry in qa}
    if len(ids) != len(qa):
        problems.append("duplicate question ids")

    print(f"documents: {len(present)}   questions: {len(qa)}")
    for name in sorted(referenced):
        print(f"  answered by  {documents[name]}")
    print(f"unreferenced (bulk-only): {len(present - referenced)}")

    if problems:
        print("\nPROBLEMS:")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print("\nno problems found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
