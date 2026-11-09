"""Release gate for the PapAuto photographic showroom on the homepage."""
from html.parser import HTMLParser
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = 24


class ShowroomParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.hrefs = []
        self.cards = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article" and "pa-car-card" in attrs.get("class", ""):
            self.cards += 1
        if tag == "img":
            self.images.append(attrs.get("src", ""))
        if tag == "a":
            self.hrefs.append(attrs.get("href", ""))


class HomeShowroom(unittest.TestCase):
    def test_rights_checked_local_photos_and_no_seller_links(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        start = html.index('<section class="pa-vitrine')
        end = html.index("</section>", start) + len("</section>")
        section = html[start:end]
        parser = ShowroomParser()
        parser.feed(section)

        self.assertEqual(parser.cards, EXPECTED)
        photos = [s for s in parser.images if s.startswith("/assets/demo/")]
        self.assertEqual(len(photos), EXPECTED)
        manifest = json.loads((ROOT / "research" / "cc0-photo-provenance.json").read_text(encoding="utf-8"))
        verified = {row["file"] for row in manifest["photos"]}
        for path in photos:
            with self.subTest(path=path):
                self.assertRegex(path, r"^/assets/demo/[a-z0-9-]+-cc0\.webp$")
                self.assertIn(path, verified)
                self.assertTrue((ROOT / path.lstrip("/")).is_file())
        self.assertEqual(len(set(photos)), EXPECTED)
        for href in parser.hrefs:
            self.assertTrue(href.startswith("/"), f"External showroom link: {href}")
        self.assertNotIn("drom", section.lower())
        self.assertNotIn("в наличии", section.lower().replace("не заявлены в наличии", ""))

    def test_page_and_build_include_showroom(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        tabs = (ROOT / "site-tabs.js").read_text(encoding="utf-8")
        build = (ROOT / "scripts" / "build_static_public.py").read_text(encoding="utf-8")
        self.assertIn('id="pa-vitrine"', html)
        self.assertIn('/showcase-visual.css', html)
        self.assertIn('/showcase-visual.js', html)
        self.assertIn("'#pa-vitrine'", tabs)
        self.assertIn('re.fullmatch(r"/assets/demo/', build)
        self.assertIn('url == "/assets/visual/fallback-vehicle.svg"', build)
        self.assertIn('assets/visual/fallback-vehicle.svg', html)


if __name__ == "__main__":
    unittest.main()
