"""PapAuto research-only auction sourcing guard for the Novosibirsk Drom sample.

Ensures the master model/year/generation matrix and the per-lot photo+sheet
evidence intake remain internally consistent without publishing unverified assets.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "research/papauto-drom991-model-year-generation-sourcing-matrix-2026-11-13.json"
JAPAN = ROOT / "research/papauto-drom991-concrete-auction-lot-photo-sheet-intake-2026-11-13.json"
CROSS = ROOT / "research/papauto-drom991-korea-china-lot-source-pool-2026-11-13.json"


class NovosibirskAuctionSourcing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        cls.jp = json.loads(JAPAN.read_text(encoding="utf-8"))
        cls.cross = json.loads(CROSS.read_text(encoding="utf-8"))

    def test_preserves_original_991_sample_limits(self):
        drom = self.matrix["based_on_drom_novosibirsk"]
        self.assertEqual(drom["reported_total_listings"], 991)
        self.assertEqual(drom["actually_reviewed_listings"], 40)
        self.assertTrue(drom["listing_sample_is_not_sales_statistics"])
        self.assertEqual(drom["prioritized_japanese_model_groups"], 32)
        self.assertEqual(self.matrix["baseline_model_directory_total"], 135)

    def test_market_model_target_counts_and_generation_search_buckets(self):
        rows = self.matrix["rows"]
        self.assertEqual(len(rows), self.matrix["sourcing_targets_total"])
        self.assertGreaterEqual(len(rows), 156)
        self.assertEqual(len({r["id"] for r in rows}), len(rows))
        by_country = {market: sum(r["market"] == market for r in rows)
                      for market in ("japan", "korea", "china")}
        self.assertEqual(by_country, self.matrix["counts_by_market"])
        self.assertEqual(by_country["korea"], 45)
        self.assertEqual(by_country["china"], 45)
        for item in rows:
            start = item["initial_auction_search_years"]["from"]
            end = item["initial_auction_search_years"]["to"]
            self.assertTrue(2010 <= start <= end <= 2026, item["id"])
            for stage in item["facelift_generation_segments"]:
                self.assertTrue(2010 <= stage["from"] <= stage["to"] <= 2026,
                                item["id"])
                self.assertFalse(stage["exact_identity_confirmed"])
            self.assertEqual(item["publish_state"], "research_queue")
            self.assertFalse(item["image_and_sheet_rights_verified"])

    def test_exact_lot_sources_have_no_fake_auction_details_or_photo_redirects(self):
        lots = self.jp["records"]
        self.assertGreaterEqual(len(lots), 18)
        self.assertEqual(len(lots), self.jp["total"])
        self.assertEqual(len({r["id"] for r in lots}), len(lots))
        self.assertEqual(len({r["original_source_page_url_research_only"] for r in lots}), len(lots))
        for lot in lots:
            self.assertEqual(lot["market"], "japan")
            self.assertTrue(lot["source_page_fetched"])
            self.assertTrue(lot["source_page_has_sheet_section"])
            self.assertTrue(lot["source_photo_urls_research_only"])
            self.assertTrue(lot["source_auction_sheet_image_candidate_url_research_only"])
            self.assertFalse(lot["source_commercial_publication_rights_verified"])
            self.assertFalse(lot["eligible_for_publication"])
            self.assertTrue(lot["no_client_external_links"])
            self.assertTrue(all("drom.ru" not in u
                                for u in lot["source_photo_urls_research_only"]))

    def test_non_japanese_aggregate_listings_are_not_labeled_full_auction_cards(self):
        rows = self.cross["sources"]
        self.assertEqual(len(rows), self.cross["korea_count"]+self.cross["china_count"])
        self.assertGreaterEqual(self.cross["korea_count"], 3)
        self.assertGreaterEqual(self.cross["china_count"], 10)
        for row in rows:
            self.assertIn(row["market"], ("korea","china"))
            self.assertFalse(row["commercial_reuse_rights_confirmed"])
            self.assertEqual(row["publish_state"], "HOLD")
        for client_page in ("gallery.html", "catalog.html"):
            public_html = (ROOT / client_page).read_text(encoding="utf-8")
            for row in rows:
                self.assertNotIn(row["source_url_research_only"], public_html)

if __name__ == "__main__":
    unittest.main()
