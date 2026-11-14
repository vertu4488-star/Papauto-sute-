"""Regression checks for the homepage: real auction-result facts, never street-photo catalogue."""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ShowcasePriceQuality(unittest.TestCase):
    def test_auction_examples_have_actual_lot_details_no_unmatched_photos(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        section = html.split('<section class="pa-vitrine', 1)[1].split("</section>", 1)[0]
        cards = re.findall(r'<article class="pa-real-lot"[^>]*>[\s\S]*?</article>', section)
        self.assertEqual(len(cards), 25)
        self.assertEqual(section.count('class="pa-real-media"'),25)
        self.assertEqual(section.count('class="pa-real-sheet"'),25)
        self.assertEqual(len(re.findall(r'<img[^>]+src="/assets/auction/home/',section)),87)
        self.assertNotIn("pa-car-photo", section)
        evidence=json.loads((ROOT/"research"/"home-auction-examples-2026-11-12.json").read_text(encoding="utf-8"))
        self.assertEqual(len(evidence["lots"]), 8)
        for card, lot in zip(cards, evidence["lots"]):
            self.assertIn(lot["make"]+" "+lot["model"],card)
            self.assertIn(str(lot["year"]),card)
            self.assertIn(lot["body"],card)
            self.assertIn(lot["auction"],card)
            self.assertIn(lot["lot"],card)
            self.assertIn("Фактическая цена продажи в Японии",card)
            self.assertIn("Пробег",card)
            self.assertIn("Оценка",card)
            self.assertIn('href="/podbor.html?similar=',card)
            self.assertNotIn("http",card)
        self.assertNotIn("≈ ",section)
        self.assertIn("без расходов до Новосибирска",section)
    def test_hero_photo_and_caption_match(self):
        html=(ROOT/"index.html").read_text(encoding="utf-8")
        css=(ROOT/"showcase-visual.css").read_text(encoding="utf-8")
        hero_css=(ROOT/"papauto-lexus-hero.css").read_text(encoding="utf-8")
        self.assertIn("Без догадок.",html)
        self.assertIn("Первый экран — согласованная рекламная иллюстрация, не аукционный лот",html)
        self.assertIn("/assets/visual/papauto-thursday-approved-editorial-artwork-20261112.webp",html)
        self.assertTrue((ROOT/"assets/visual/papauto-thursday-approved-editorial-artwork-20261112.webp").is_file())
        self.assertNotIn('href="/assets/visual/papauto-thursday-approved-editorial-artwork-20261112.webp"',html)
        self.assertNotIn("На фото Kia K5",html)
        self.assertIn("/assets/auction/home/toyota-corolla-sport-2023-20038-photo-1.jpg",hero_css)
        self.assertTrue((ROOT/"assets/auction/home/toyota-corolla-sport-2023-20038-photo-1.jpg").is_file())
        self.assertIn('/papauto-lexus-hero.css',html)
        self.assertIn('href="/?view=calculator"',html)
        self.assertIn("pa-vitrine-grid{grid-template-columns:1fr",css)

if __name__=="__main__":
    unittest.main()
