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
        # The CSV export intentionally uses a.href=url for a local Blob download.
        # Only prohibit using external source URLs as navigable links.
        self.assertNotIn("a.href=r.source_url", js)
        self.assertNotIn("a.href=r.sheet_url", js)

    def test_dynamic_source_links(self):
        homepage = (ROOT / "app.js").read_text(encoding="utf-8")
        for forbidden in (
            "banzai24.com", "www.ttpai.cn", "a.href=record.url",
            "a.href=source.url", "a.href=data.source_url",
            "a.href=item.listing_url",
        ):
            self.assertNotIn(forbidden, homepage)

    def test_chassis_search_does_not_send_client_outside(self):
        js = (ROOT / "japan-chassis-search.js").read_text(encoding="utf-8")
        for forbidden in ("google.com/search", "banzai24.com", "carvector.com", "jpsheet.com"):
            self.assertNotIn(forbidden, js)
        self.assertIn('link.href="/?view=select', js)

    def test_smart_search_keeps_buyer_on_papauto(self):
        js = (ROOT / "smart-search.js").read_text(encoding="utf-8")
        self.assertNotIn("a.href=url", js)
        self.assertNotIn("a.target=\"_blank\"", js)
        self.assertIn('a.href="/?view=select#assistant"', js)

    def test_legacy_drom_pages_not_published(self):
        for legacy_page in (
            "drom-novosibirsk-2026.html",
            "novosibirsk-avto-bez-probega-2026.html",
        ):
            self.assertFalse((ROOT / legacy_page).exists(), legacy_page)

    def test_public_assets_contain_no_drom_traces(self):
        import re

        public_assets = (
            list(ROOT.glob("*.html"))
            + list(ROOT.glob("*.js"))
            + list((ROOT / "data").glob("*.json"))
            + [ROOT / "sitemap.xml"]
        )
        stale = [
            path.name
            for path in public_assets
            if re.search(r"drom|дром", path.read_text(encoding="utf-8"), re.I)
        ]
        self.assertEqual(stale, [], "Drom legacy mentions remain in public assets")

if __name__ == "__main__":
    unittest.main()
