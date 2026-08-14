"""Figure description: the cache, HTML source resolution, and degradation.

Fixtures only — no models, no network. The API call itself is stubbed; what is
under test is everything around it, which is where the failure modes live: a
second run must cost nothing, HTML figures must be found on disk because Docling
does not carry their bytes, and no failure may cost a document its prose.
"""
import json
from pathlib import Path

import pytest
from PIL import Image

from ingestion import describe

pytestmark = pytest.mark.ingest


def _png(tmp_path: Path, name: str, colour: str = "red") -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), colour).save(path)
    return path


class TestCache:
    def test_round_trips_through_the_file(self, tmp_path: Path) -> None:
        cache = describe._Cache(tmp_path / "d.json")
        cache.put("abc", "a bar chart")

        assert describe._Cache(tmp_path / "d.json").get("abc") == "a bar chart"

    def test_missing_file_is_an_empty_cache(self, tmp_path: Path) -> None:
        assert describe._Cache(tmp_path / "absent.json").get("abc") is None

    def test_corrupt_file_does_not_raise(self, tmp_path: Path) -> None:
        """A bad cache costs API calls, not a run."""
        path = tmp_path / "d.json"
        path.write_text("{not json", encoding="utf-8")

        assert describe._Cache(path).get("abc") is None

    def test_written_as_readable_utf8(self, tmp_path: Path) -> None:
        """Descriptions are in the document's language — German here."""
        path = tmp_path / "d.json"
        describe._Cache(path).put("k", "Restkapazität bei −10 °C")

        assert "Restkapazität" in json.loads(path.read_text(encoding="utf-8"))["k"]


class TestImageHash:
    def test_same_pixels_hash_alike(self, tmp_path: Path) -> None:
        """Keyed by content, so one figure reused across documents costs one call."""
        one = Image.open(_png(tmp_path, "a.png"))
        two = Image.open(_png(tmp_path, "b.png"))

        assert describe._hash(one) == describe._hash(two)

    def test_different_pixels_differ(self, tmp_path: Path) -> None:
        one = Image.open(_png(tmp_path, "a.png", "red"))
        two = Image.open(_png(tmp_path, "b.png", "blue"))

        assert describe._hash(one) != describe._hash(two)


class TestHtmlImagePaths:
    """Docling yields no image bytes for HTML, so they come off disk instead."""

    def test_resolves_relative_to_the_document(self, tmp_path: Path) -> None:
        _png(tmp_path, "images/chart.png")
        page = tmp_path / "faq.html"
        page.write_text('<p>x</p><img src="images/chart.png" alt="">', encoding="utf-8")

        assert describe.html_image_paths(page) == [(tmp_path / "images/chart.png").resolve()]

    def test_preserves_document_order(self, tmp_path: Path) -> None:
        """Pictures are matched to sources positionally, so order is load-bearing."""
        page = tmp_path / "faq.html"
        page.write_text('<img src="one.png"><img src="two.png">', encoding="utf-8")

        assert [p.name for p in describe.html_image_paths(page)] == ["one.png", "two.png"]

    def test_handles_single_quotes_and_extra_attributes(self, tmp_path: Path) -> None:
        page = tmp_path / "faq.html"
        page.write_text("<img class='fig' src='a.png' width='40'>", encoding="utf-8")

        assert [p.name for p in describe.html_image_paths(page)] == ["a.png"]

    def test_no_images_is_not_an_error(self, tmp_path: Path) -> None:
        page = tmp_path / "faq.html"
        page.write_text("<p>no figures here</p>", encoding="utf-8")

        assert describe.html_image_paths(page) == []

    def test_unreadable_document_returns_nothing(self, tmp_path: Path) -> None:
        assert describe.html_image_paths(tmp_path / "absent.html") == []
