"""Release gate for auction photos: license evidence and self-hosted files required."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "approved-auction-lots.json"
MEDIA = ROOT / "assets" / "auction"
PHOTO = re.compile(r"^/assets/auction/[a-zA-Z0-9_.\-/]+\.(?:jpe?g|png|webp)$")
COUNTRIES = {"japan", "south-korea", "china"}


class ApprovedAuctionMedia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.lots = cls.doc.get("lots", [])

    def test_list_and_uniqueness(self):
        self.assertIsInstance(self.lots, list)
        ids = [r.get("id") for r in self.lots]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate auction lot IDs")

    def test_every_published_image_is_local_and_licensed(self):
        for r in self.lots:
            with self.subTest(lot=r.get("id")):
                self.assertIn(r.get("country"), COUNTRIES)
                self.assertTrue(r.get("id") and r.get("make") and r.get("model"))
                self.assertTrue(1950 <= int(r.get("year", 0)) <= 2027)
                self.assertEqual(r.get("image_rights"), "approved")
                self.assertTrue(r.get("rights_holder"))
                self.assertTrue(r.get("rights_reference"))
                self.assertTrue(r.get("commercial_use_permission"))
                self.assertTrue(r.get("self_host_permission"))
                self.assertTrue(r.get("sheet_permission"))
                self.assertIsInstance(r.get("auction_sheet"), str)
                self.assertRegex(r["auction_sheet"], PHOTO)
                self.assertNotIn("..", r["auction_sheet"])
                sheet = ROOT / r["auction_sheet"].lstrip("/")
                self.assertTrue(sheet.resolve().is_relative_to(MEDIA.resolve()))
                self.assertTrue(sheet.is_file(), f"Missing auction sheet: {r['auction_sheet']}")
                content = sheet.read_bytes()
                self.assertGreater(len(content), 500)
                self.assertTrue(content.startswith(b"\xff\xd8\xff")
                                or content.startswith(b"\x89PNG\\r\\n\x1a\\n")
                                or (content.startswith(b"RIFF") and content[8:12] == b"WEBP"))
                photos = r.get("photos")
                self.assertIsInstance(photos, list)
                self.assertGreater(len(photos), 0)
                for name in photos:
                    self.assertIsInstance(name, str)
                    self.assertRegex(name, PHOTO)
                    self.assertNotIn("..", name)
                    full = ROOT / name.lstrip("/")
                    self.assertTrue(full.resolve().is_relative_to(MEDIA.resolve()))
                    self.assertTrue(full.is_file(), f"Missing local photo: {name}")
                    self.assertGreater(full.stat().st_size, 500)
                    magic = full.read_bytes()[:12]
                    self.assertTrue(
                        magic.startswith(b"\xff\xd8\xff")
                        or magic.startswith(b"\x89PNG\r\n\x1a\n")
                        or (magic.startswith(b"RIFF") and magic[8:12] == b"WEBP"),
                        f"Invalid image format: {name}"
                    )

    def test_authorized_media_importer_compiles(self):
        importer = ROOT / "scripts" / "import_auction_photos.py"
        compile(importer.read_text(encoding="utf-8"), str(importer), "exec")

    def test_price_is_not_presented_as_proven_without_evidence(self):
        for r in self.lots:
            with self.subTest(lot=r.get("id")):
                if r.get("sale_status") == "verified_sold":
                    self.assertTrue(r.get("sale_evidence_reference"))
                    self.assertTrue(r.get("sold_date"))
                    self.assertIn(r.get("currency"), {"JPY", "KRW", "CNY"})
                    self.assertGreater(float(r.get("sold_price", 0)), 0)

    def test_source_urls_do_not_leak_to_public_catalog(self):
        for r in self.lots:
            self.assertFalse(
                any(k in r for k in ("source_url", "listing_url", "photo_url", "sheet_url")),
                "Internal supplier URLs must not appear in public data."
            )


if __name__ == "__main__":
    unittest.main()
