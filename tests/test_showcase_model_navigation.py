"""Regression checks: model-detail pages remain reachable via catalog after moving street photos off the homepage."""
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
        self.assertIn('href="/catalog.html"', home)
        self.assertIn('id="pa-vitrine"', home)
        self.assertIn("РЕАЛЬНЫЕ РЕЗУЛЬТАТЫ ТОРГОВ", home)
        self.assertEqual(home.count('class="pa-real-lot"'), 25)
        self.assertNotIn('class="pa-car-card"', home)
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
