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
    def test_removed_street_photos_and_no_seller_links(self):
        """Keep 24 working model cards but do not show heterogeneous street photos."""
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        start = html.index('<section class="pa-vitrine')
        end = html.index("</section>", start) + len("</section>")
        section = html[start:end]
        parser = ShowroomParser()
        parser.feed(section)

        self.assertEqual(parser.cards, EXPECTED)
        self.assertFalse(parser.images, "Model photos must stay hidden until auction media is approved")
        self.assertEqual(section.count('class="pa-auction-pending"'), EXPECTED)
        self.assertIn("auction-photo-hold.css", html)
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
        self.assertIn('/auction-photo-hold.css', html)


if __name__ == "__main__":
    unittest.main()
