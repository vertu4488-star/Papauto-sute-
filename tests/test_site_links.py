"""Verify that every PAPAUTO sitemap page and internal HTML asset link resolves.

No network calls, customer data or paid services. Runs during predeploy CI.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import posixpath
import json
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HOSTS = {"papauto.ru", "www.papauto.ru"}
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
# Only these four published files are created from pinned MIT SurveyJS package
# archives at build time; they intentionally do not live in the repository.
from scripts.vendor_surveyjs import ASSETS as SURVEYJS_ASSETS
BUILT_VENDOR_FILES = {
    ROOT / "vendor" / "surveyjs" / filename for filename in SURVEYJS_ASSETS
}

def built_exact_auction_files():
    """Pinned, exact-lot photos/materials created by the public static build."""
    doc = json.loads((ROOT / "research" / "home-8-exact-lot-photo-sheet-references-2026-11-12.json").read_text(encoding="utf-8"))
    records = doc.get("records", [])
    if len(records) != 25:
        raise RuntimeError("Unexpected number of pinned auction photo lots")
    out = set()
    for entry in records:
        slug = entry["slug"]
        if not slug or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in slug):
            raise RuntimeError("Invalid auction lot slug")
        photos = entry["auction_photos"]
        for idx, url in enumerate(photos, 1):
            out.add(ROOT / "assets" / "auction" / "home" / f"{slug}-photo-{idx}.jpg")
        out.add(ROOT / "assets" / "auction" / "home" / f"{slug}-sheet.jpg")
    return out

BUILT_AUCTION_FILES = built_exact_auction_files()

def built_auction_detail_pages():
    """Known exact-lot URLs are materialized by the static site builder.
    No arbitrary /lots/ path is implicitly trusted.
    """
    if not (ROOT/"scripts/generate_auction_lot_pages.py").is_file():
        raise RuntimeError("Auction detail page generator missing")
    # The checked-in 37-row HTML template is an input to the publisher;
    # two outdoor-only template records are intentionally removed from release.
    # The final gallery is compiled to render-public with 639 approved records.
    # Source links are legitimate during source inspection, but final links
    # must also point to an actual generated detail page.
    approved_pages = set()
    input_path = ROOT / "data" / "gallery-lots.json"
    final_path = ROOT / "render-public" / "data" / "gallery-lots.json"
    for source, is_final in [(input_path, False), (final_path, True)]:
        if not source.is_file():
            continue
        gallery = json.loads(source.read_text(encoding="utf-8"))
        for lot in gallery["lots"]:
            lot_id = lot["id"]
            if (not lot_id or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in lot_id)
                    or not lot.get("photos") or not lot.get("inspection_image")
                    or not lot.get("description")):
                raise RuntimeError("Incomplete auction source lot: " + str(lot_id))
            detail = Path("lots") / (lot_id + ".html")
            if is_final and not (ROOT / "render-public" / detail).is_file():
                raise RuntimeError("Published lot page not generated: " + str(detail))
            approved_pages.add(ROOT / detail)
    return approved_pages


BUILT_LOT_PAGES = built_auction_detail_pages()


class Links(HTMLParser):
    """Only inspect URL-valued HTML attributes, not JavaScript or text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a":
            key = "href"
        elif tag == "link":
            key = "href"
        elif tag in ("script", "img", "source", "iframe"):
            key = "src"
        else:
            return
        url = a.get(key)
        if url:
            self.links.append((tag, url))


def local_target(page: Path, raw: str):
    if raw.startswith("//"):
        return None
    parsed = urlsplit(raw)
    if parsed.scheme not in ("", "http", "https"):
        return None
    if parsed.netloc and parsed.hostname not in HOSTS:
        return None
    if not parsed.path:
        return None  # Same-page fragments or query-only links.
    path = unquote(parsed.path).replace("\\", "/")
    if path.startswith("/"):
        resolved = posixpath.normpath(path)
    else:
        parent = "/" + page.relative_to(ROOT).parent.as_posix().lstrip(".")
        resolved = posixpath.normpath(posixpath.join(parent, path))
    if not resolved.startswith("/"):
        return None
    if path.endswith("/") or resolved == "/":
        resolved = resolved.rstrip("/") + "/index.html"
    return ROOT / resolved.lstrip("/")


class PAPAUTOLinksTest(unittest.TestCase):
    def test_sitemap_all_targets_are_real_pages(self):
        urls = [el.text for el in ET.parse(ROOT / "sitemap.xml").iter(SITEMAP_NS)]
        self.assertGreaterEqual(len(urls), 30, "Unexpectedly small sitemap")
        for raw in urls:
            with self.subTest(url=raw):
                target = local_target(ROOT / "index.html", raw)
                self.assertIsNotNone(target)
                self.assertTrue(target.is_file(), f"Missing sitemap page: {raw}")

    def test_public_html_has_no_broken_local_links(self):
        # Generated SEO pages are at repo root; do not parse non-public sources.
        html_files = list(ROOT.glob("*.html"))
        self.assertGreaterEqual(len(html_files), 30)
        errors = []
        for page in html_files:
            parsed = Links()
            parsed.feed(page.read_text(encoding="utf-8"))
            for tag, raw in parsed.links:
                target = local_target(page, raw)
                if target is not None and not target.is_file() and target not in BUILT_VENDOR_FILES and target not in BUILT_AUCTION_FILES and target not in BUILT_LOT_PAGES:
                    errors.append(f"{page.name}: {tag} {raw} -> {target.relative_to(ROOT)}")
        self.assertEqual(errors, [], "\n".join(errors[:40]))


if __name__ == "__main__":
    unittest.main()
