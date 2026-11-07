"""Prevent PapAuto visitors being sent to competitors through public HTML links.

Run: python -m unittest tests.test_no_external_sales_links
"""
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class PublicAnchors(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.external = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        props = dict(attrs)
        href = (props.get("href") or "").strip()
        if not href:
            return
        absolute = href if not href.startswith("//") else "https:" + href
        if not absolute.lower().startswith(("https://", "http://")):
            return
        u = urlsplit(absolute)
        if u.hostname not in {"papauto.ru", "www.papauto.ru"}:
            self.external.append(href)

class NoExternalSellerLinks(unittest.TestCase):
    def test_public_html_keeps_visitors_in_papauto(self):
        failures = []
        for path in sorted(ROOT.glob("*.html")):
            parser = PublicAnchors()
            parser.feed(path.read_text(encoding="utf-8"))
            for href in parser.external:
                failures.append(f"{path.name}: {href}")
        self.assertFalse(failures, "Внешние клиентские переходы запрещены:\\n" + "\\n".join(failures))

    def test_auction_archive_does_not_open_source_urls(self):
        path = ROOT / "auction-archive.js"
        if not path.exists():
            return
        js = path.read_text(encoding="utf-8")
        self.assertNotIn("a.target='_blank'", js)
        # The CSV export intentionally uses a.href=url for a local Blob download.\n        # Only prohibit using external source URLs as navigable links.\n        self.assertNotIn("a.href=r.source_url", js)\n        self.assertNotIn("a.href=r.sheet_url", js)

if __name__ == "__main__":
    unittest.main()
