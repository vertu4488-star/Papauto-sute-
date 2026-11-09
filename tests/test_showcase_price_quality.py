"""Regression gate: every PapAuto showroom card must explain the model and price status."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ShowcasePriceQuality(unittest.TestCase):
    def test_24_cards_have_specific_model_details_and_honest_market_reference(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        section = html.split('<section class="pa-vitrine', 1)[1].split("</section>", 1)[0]
        cards = re.findall(r'<article class="pa-car-card"[^>]*>[\s\S]*?</article>', section)
        self.assertEqual(len(cards), 24)
        prices, models, notes = 0, [], []
        for card in cards:
            name = re.search(r"<h3>([^<]+)</h3>", card)
            self.assertIsNotNone(name)
            models.append(name.group(1))
            self.assertIn('class="pa-photo-type"', card)
            self.assertIn('class="pa-car-meta"', card)
            self.assertIn('class="pa-car-price"', card)
            self.assertIn('class="pa-car-note"', card)
            self.assertNotIn("Стоимость — по запросу", card)
            self.assertNotIn("Наличие, год, пробег и итоговая цена уточняются", card)
            self.assertIn("Рассчитать", card)
            note = re.search(r'<p class="pa-car-note">([^<]+)</p>', card)
            self.assertIsNotNone(note)
            notes.append(note.group(1))
            if "Рыночный ориентир" in card:
                prices += 1
                self.assertRegex(card, r"≈ [\d\s]+ ₽")
            else:
                self.assertIn("По расчёту", card)
        self.assertEqual(len(set(models)), 24)
        self.assertGreaterEqual(len(set(notes)), 20)
        self.assertEqual(prices, 24)
        self.assertIn("не цены продажи PAPAUTO", section)
        self.assertIn("до Владивостока", section)
        self.assertIn("медиана", section)
        self.assertIn("минимум", section)
        self.assertNotIn("href=\"https://", section)

    def test_hero_photo_and_caption_match(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "showcase-visual.css").read_text(encoding="utf-8")
        self.assertIn("На фото Kia K5", html)
        self.assertIn("url('/assets/demo/kia-k5-cc0.webp')", css)
        self.assertNotIn("url('/assets/demo/honda-freed-hybrid-cc0.webp')", css)
        self.assertIn("pa-vitrine-grid{grid-template-columns:1fr", css)


if __name__ == "__main__":
    unittest.main()
