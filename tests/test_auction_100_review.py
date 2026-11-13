"""Full set of 100 raw Japan/China lead sources stay PRIVATE and not publishable."""
import json
import unittest
from pathlib import Path
from scripts.generate_auction_100_review import audited_batch, render

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"research/auction-100-japan-china-intake-2026-11-13.json"
OUTPUT=ROOT/"research/auction-100-japan-china-review.html"

class ResearchQueueTest(unittest.TestCase):
    def setUp(self):
        self.doc=json.loads(SOURCE.read_text(encoding="utf-8"))
    def test_all_100_sources_have_per_lot_checklist(self):
        rows=audited_batch(self.doc)
        self.assertEqual(len(rows),100)
        self.assertEqual(sum(x["target_market"]=="japan" for x in rows),90)
        self.assertEqual(sum(x["target_market"]=="china" for x in rows),10)
        self.assertEqual(sum(bool(x["ready_for_publication"]) for x in rows),0)
    def test_private_dashboard_is_reproducible_and_has_no_external_images(self):
        expected=render(self.doc)
        self.assertEqual(expected,OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(expected.count('class="lot"'),100)
        self.assertEqual(expected.count('class="source"'),100)
        self.assertIn('name="robots" content="noindex,nofollow"',expected)
        self.assertNotIn("<img",expected)
        self.assertNotIn("https://8.ajes.com",expected)
        self.assertNotIn("https://img.plc.auction",expected)
        self.assertNotIn('href="/lots/',expected)
    def test_public_gallery_unchanged(self):
        gallery=json.loads((ROOT/"data/gallery-lots.json").read_text(encoding="utf-8"))
        approved=json.loads((ROOT/"data/approved-auction-lots.json").read_text(encoding="utf-8"))
        self.assertEqual(len(gallery["lots"]),37)
        self.assertEqual(len(approved["lots"]),0)
        assert all(lot["inspection_kind"]=="Аукционный лист" for lot in gallery["lots"])
        self.assertFalse((ROOT/"auction-100-japan-china-review.html").exists())

if __name__=="__main__":unittest.main()
