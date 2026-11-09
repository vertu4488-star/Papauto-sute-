"""Guard the self-hosted details pages linked by PapAuto's 24-card showcase."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

EXPECTED = {
    "hyundai-sonata", "hyundai-tucson", "kia-sportage",
    "kia-seltos", "hyundai-santa-fe", "kia-carnival",
    "geely-coolray", "geely-emgrand", "byd-song-plus",
    "byd-dolphin", "changan-uni-v", "changan-cs55-plus",
    "haval-jolion",
}


class ShowcaseModelNavigation(unittest.TestCase):
    def test_details_are_internal_and_complete(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        html = (ROOT / "showcase-model-detail.html").read_text(encoding="utf-8")
        script = (ROOT / "showcase-model-detail.js").read_text(encoding="utf-8")
        cards = re.findall(r'<article class="pa-car-card"[^>]*>[\s\S]*?</article>', home)
        self.assertEqual(len(cards), 24)
        linked = set()
        for card in cards:
            detail = re.search(r'<a href="([^"]+)">Подробнее</a>', card)
            self.assertIsNotNone(detail)
            href = detail.group(1)
            self.assertTrue(href.startswith("/"), href)
            self.assertNotIn("drom", href.lower())
            if href.startswith("/showcase-model-detail.html?model="):
                linked.add(href.partition("?model=")[2])
            else:
                self.assertTrue(href.endswith(".html"), href)
        self.assertSetEqual(linked, EXPECTED)
        self.assertIn("showcase-model-detail.js", html)
        self.assertIn('content="noindex,follow"', html)
        for slug in EXPECTED:
            self.assertIn('["' + slug + '",', script)
        self.assertIn('cache:"no-store"', script)
        self.assertIn('encodeURIComponent(name)', script)
        self.assertNotIn("https://drom", html + script)

    def test_there_is_no_false_inventory_claim_in_details(self):
        html = (ROOT / "showcase-model-detail.html").read_text(encoding="utf-8")
        self.assertIn("не снимок предлагаемого автомобиля", html)
        self.assertIn("не цена сделки", html)
        self.assertIn("до Новосибирска", html)


if __name__ == "__main__":
    unittest.main()
