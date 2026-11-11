"""Verify that every PAPAUTO sitemap page and internal HTML asset link resolves.

No network calls, customer data or paid services. Runs during predeploy CI.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import posixpath
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
                if target is not None and not target.is_file() and target not in BUILT_VENDOR_FILES:
                    errors.append(f"{page.name}: {tag} {raw} -> {target.relative_to(ROOT)}")
        self.assertEqual(errors, [], "\n".join(errors[:40]))


if __name__ == "__main__":
    unittest.main()
