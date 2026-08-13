"""The api must not pull in the parsing stack.

The split between the two images is what keeps parsing — layout, table structure
and OCR models, the larger half of the ingest image — out of the request path.
That boundary is enforced at build time by a dependency group, which means an
accidental `import docling` in api code only shows up as a container that will
not start. This catches it in the fast suite instead.

The embedder is a different case: the api genuinely needs it, because a query
must be embedded with the same model the corpus was indexed with.
"""
import subprocess
import sys

# A subprocess, not this one: the ingest tests import docling directly, so by
# the time this runs `sys.modules` says nothing about what the api pulled in.
PROBE = """
import sys
import app.main  # noqa: F401
print(",".join(sorted(m for m in sys.modules if m.startswith("docling"))))
"""


def test_the_api_does_not_import_docling() -> None:
    result = subprocess.run(
        [sys.executable, "-c", PROBE],
        capture_output=True,
        text=True,
        check=True,
    )

    leaked = result.stdout.strip()

    assert not leaked, (
        f"docling reached the api process via {leaked.split(',')[0]} — it is not "
        "installed in the api image, so the container would fail to start"
    )
