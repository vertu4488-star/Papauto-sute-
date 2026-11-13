"""100-source intake must NEVER bypass genuine-auction-sheet and rights gate."""
import json
import unittest
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/"research/auction-100-japan-china-intake-2026-11-13.json"
GALLERY=ROOT/"data/gallery-lots.json"
APPROVED=ROOT/"data/approved-auction-lots.json"

class Intake100Safe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=json.loads(BATCH.read_text(encoding="utf-8"))
        cls.records=cls.doc["records"]
    def test_exactly_100_source_pages_diversified_by_country(self):
        self.assertEqual(len(self.records),100)
        self.assertEqual(Counter(r["target_market"] for r in self.records),
                         {"japan":90,"china":10})
        self.assertEqual(len({r["source_url_research_only"] for r in self.records}),100)
        self.assertEqual(len({r["work_id"] for r in self.records}),100)
        self.assertEqual(sum(len(r["external_photo_references_research_only"]) for r in self.records),140)
    def test_no_unverified_auction_photos_or_fake_sheets_can_publish(self):
        for row in self.records:
            self.assertFalse(row["ready_for_publication"])
            self.assertEqual(row["publication_state"],"BLOCKED_SOURCE_RESEARCH")
            self.assertIsNone(row["matching_full_original_auction_sheet_file"])
            self.assertIsNone(row["auction_house"])
            self.assertIsNone(row["authentic_auction_lot_number"])
            self.assertIsNone(row["source_mileage_km"])
            self.assertIsNone(row["source_grade"])
            self.assertIsNone(row["written_photo_commercial_selfhost_license"])
            self.assertIsNone(row["written_sheet_commercial_selfhost_license"])
            self.assertEqual(row["verified_original_auction_photo_files"],[])
            self.assertGreaterEqual(len(row["external_photo_references_research_only"]),1)
    def test_public_gallery_and_approved_import_unmodified(self):
        gallery=json.loads(GALLERY.read_text(encoding="utf-8"))
        approved=json.loads(APPROVED.read_text(encoding="utf-8"))
        self.assertEqual(len(gallery["lots"]),37)
        self.assertEqual(len(approved["lots"]),0)
        self.assertTrue(all(row.get("inspection_kind")=="Аукционный лист"
                            for row in gallery["lots"]))
        source=(ROOT/"gallery.html").read_text(encoding="utf-8")
        for row in self.records:
            self.assertNotIn(row["source_url_research_only"],source)
        self.assertEqual(source.count('class="gallery-card"'),37)
if __name__=="__main__":
    unittest.main()
