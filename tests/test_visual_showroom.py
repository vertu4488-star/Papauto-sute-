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
        """Show the 24 self-hosted licensed model photos and eight popular models without false auction claims."""
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        start = html.index('<section class="pa-vitrine')
        end = html.index("</section>", start) + len("</section>")
        section = html[start:end]
        parser = ShowroomParser()
        parser.feed(section)

        self.assertEqual(parser.cards, EXPECTED)
        self.assertEqual(len(parser.images), EXPECTED + 8, "24 catalog photos and 8 featured model photos")
        self.assertEqual(section.count('class="pa-car-photo pa-licensed-photo"'), EXPECTED)
        self.assertNotIn('class="pa-auction-pending"', section)
        provenance = json.loads((ROOT / "research" / "cc0-photo-provenance.json").read_text(encoding="utf-8"))
        licensed = {
            item["file"] for item in provenance["photos"]
            if "CC0" in item.get("rights", "") or "CC BY-SA" in item.get("rights", "")
        }
        for src in parser.images:
            self.assertRegex(src, r"^/assets/demo/[a-z0-9-]+\.webp$", "Only local model photos are allowed")
            self.assertIn(src, licensed, f"Missing rights provenance: {src}")
            self.assertTrue((ROOT / src.lstrip("/")).is_file(), f"Missing model photo: {src}")
        self.assertIn("Фото модели", section)
        self.assertIn("не изображения конкретных аукционных лотов", section)
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
