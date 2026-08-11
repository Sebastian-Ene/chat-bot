"""Where corpus sources live, and where the generated documents go.

Sources (Markdown, figures) sit under `scripts/`; only rendered documents land in
`corpus/`. The output tree is deliberately nested — the ingester is expected to
walk it recursively rather than read one flat directory.
"""
import shutil
from pathlib import Path

# Sources — inputs to generation, not part of the deliverable corpus.
SOURCE = Path("scripts/corpus")
CONTENT = SOURCE / "content"
IMAGES = SOURCE / "images"

# Output — committed.
CORPUS = Path("corpus")
DOCS_INITIAL = CORPUS / "docs-initial"
COVERAGE = DOCS_INITIAL / "coverage"
BULK = DOCS_INITIAL / "bulk"
DOCS_LATER = CORPUS / "docs-later"

IMAGE_SUBDIR = "images"


def image_source(reference: str) -> Path:
    """Resolve an `images/foo.png` reference in content to its source file."""
    return IMAGES / Path(reference).name


def copy_images(references: list[str], out_dir: Path) -> list[Path]:
    """Place images beside an HTML document.

    PDF and DOCX embed their figures at build time, so only HTML needs this —
    it references images by relative path.
    """
    if not references:
        return []
    target = out_dir / IMAGE_SUBDIR
    target.mkdir(parents=True, exist_ok=True)
    copied = []
    for reference in references:
        source = image_source(reference)
        destination = target / source.name
        shutil.copyfile(source, destination)
        copied.append(destination)
    return copied
