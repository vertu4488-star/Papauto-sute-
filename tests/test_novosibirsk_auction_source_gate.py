"""Candidate-source intake only: never auto-publish unreviewed third-party auction media."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "research/novosibirsk-next-six-auction-candidates-2026-11-13.json"
GALLERY = ROOT / "data/gallery-lots.json"

class NovosibirskAuctionSourceGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intake = json.loads(CANDIDATES.read_text(encoding="utf-8"))
        cls.gallery = json.loads(GALLERY.read_text(encoding="utf-8"))

    def test_six_real_model_sources_have_distinct_references(self):
        rows = self.intake["records"]
        self.assertEqual(len(rows), 6)
        self.assertEqual(self.intake["candidate_count"], len(rows))
        self.assertEqual(len({r["source_url_research_only"] for r in rows}), 6)
        self.assertEqual(
            {r["model"] for r in rows},
            {"Toyota Passo", "Honda Freed Spike", "Toyota Noah",
             "Toyota Voxy", "Toyota Vitz", "Toyota C-HR"}
        )
        self.assertTrue(all(r["source_url_research_only"].startswith("https://") for r in rows))
        self.assertTrue(all("drom.ru" not in r["source_url_research_only"] for r in rows))

    def test_auction_photos_and_rights_are_blocked_by_default(self):
        self.assertTrue(self.intake["explicitly_no_street_photos"])
        self.assertTrue(self.intake["explicitly_no_drom_photos"])
        for row in self.intake["records"]:
            self.assertFalse(row["photos_individually_visually_reviewed"])
            self.assertFalse(row["photos_confirmed_auction_setting"])
            self.assertFalse(row["full_original_sheet_downloaded_and_matched"])
            self.assertFalse(row["written_commercial_media_permission"])
            self.assertFalse(row["public_auction_card_ready"])
            self.assertEqual(row["public_asset_paths"], [])

    def test_unchanged_public_gallery(self):
        self.assertEqual(self.intake["public_lot_count_unchanged"], 37)
        self.assertEqual(self.intake["new_public_lots"], 0)
        self.assertEqual(self.gallery["lot_count"], 37)
        ids = {lot["id"] for lot in self.gallery["lots"]}
        self.assertFalse(ids.intersection({r["id"] for r in self.intake["records"]}))
        for page in ("gallery.html", "gallery.js"):
            markup = (ROOT / page).read_text(encoding="utf-8")
            for row in self.intake["records"]:
                self.assertNotIn(row["source_url_research_only"], markup)

if __name__ == "__main__":
    unittest.main()
