"""Generate the test document corpus and its golden Q&A set.

    uv run python -m scripts.generate_corpus

Sources live under `scripts/corpus/` (Markdown content, generated figures);
only rendered documents land in `corpus/`, in a nested tree the ingester is
expected to walk recursively:

    corpus/docs-initial/coverage/    hand-authored, carries the hard aspects
    corpus/docs-initial/bulk/        distractors
    corpus/docs-later/               second batch, for incremental ingestion

Output is committed: the deliverable is a single zip, and a reviewer should have
documents to ingest without running a generator first.
"""
from scripts.corpus import (
    doc1_installation,
    doc2_technische_daten,
    doc3_warranty,
    doc4_garantie,
    doc5_faq,
    error_codes,
    golden_qa,
    images,
    markdown_kit,
    paths,
    renderers,
)


def main() -> None:
    for directory in (paths.COVERAGE, paths.BULK, paths.DOCS_LATER):
        directory.mkdir(parents=True, exist_ok=True)

    print("figures (sources):")
    for name, path in images.build_all(paths.IMAGES).items():
        print(f"  {name:16} {path}")

    coverage = [
        ("EN · PDF  · installation", doc1_installation.build),
        ("DE · PDF  · technical", doc2_technische_daten.build),
        ("EN · DOCX · warranty", doc3_warranty.build),
        ("DE · DOCX · garantie", doc4_garantie.build),
        ("EN+DE · HTML · faq", doc5_faq.build),
    ]
    print(f"coverage → {paths.COVERAGE}:")
    for label, build in coverage:
        path = build(paths.COVERAGE)
        print(f"  {label:26} {path.name:44} {path.stat().st_size / 1024:7.1f} KB")

    error_codes.write(paths.CONTENT)
    targets = {"initial": paths.BULK, "later": paths.DOCS_LATER}
    for batch, out_dir in targets.items():
        print(f"{batch} → {out_dir}:")
        for source in sorted(paths.CONTENT.glob("*.md")):
            doc = markdown_kit.parse(source)
            if doc.batch != batch:
                continue
            path = renderers.render(doc, out_dir, source.stem)
            print(
                f"  {doc.lang} · {doc.fmt:4} · {doc.layout:6} {path.name:38} "
                f"{path.stat().st_size / 1024:7.1f} KB"
            )

    qa_path = golden_qa.write(paths.CORPUS / "golden_qa.json")
    print(
        f"golden set: {qa_path} ({len(golden_qa.QA)} initial + "
        f"{len(golden_qa.LATER_QA)} later)"
    )
    for kind, count in sorted(golden_qa.summary().items()):
        print(f"  {kind:15} {count}")


if __name__ == "__main__":
    main()
