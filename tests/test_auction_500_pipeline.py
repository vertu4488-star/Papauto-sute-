"""The 500-card pipeline must reject generic imagery and preserve true lot-to-sheet identity."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.import_auction_photos import normalize_lot
from scripts.compile_auction_gallery import compile_published_gallery

ROOT = Path(__file__).resolve().parents[1]


class AuctionOnlyExpansionPipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.media = self.base / "intake"
        self.media.mkdir()
        # Test-only synthetic JPEG signatures, never published or imported to the repository.
        (self.media / "lot.jpg").write_bytes(b"\xff\xd8\xff" + b"\x00" * 3050)
        (self.media / "sheet.jpg").write_bytes(b"\xff\xd8\xff" + b"\x01" * 3050)
        self.row = {
            "id": "lot-korea-approved-test-001",
            "country": "south-korea", "make": "Hyundai", "model": "Avante",
            "year": 2021, "auction": "Lotte Auto Auction", "lot": "771",
            "auction_date": "2026-05-12", "grade": "4.5", "mileage_km": 42000,
            "description": "Auction vehicle with matching inspection document and original listing provenance.",
            "photos": ["lot.jpg"], "auction_sheet": "sheet.jpg",
            "photo_context": "original_auction_lot",
            "photo_evidence": [{"file": "lot.jpg", "capture_type": "auction_house_lot_photo",
                                "auction": "Lotte Auto Auction", "lot": "771",
                                "auction_date": "2026-05-12", "proof_reference": "internal-test-record"}],
            "sheet_evidence": {"file": "sheet.jpg", "document_type": "original_auction_sheet",
                               "auction": "Lotte Auto Auction", "lot": "771",
                               "auction_date": "2026-05-12", "proof_reference": "internal-test-sheet"},
            "vehicle_evidence_reference": "internal-test-vehicle-record",
            "rights": {"holder": "Test Rights Holder", "evidence_reference": "test-license",
                       "commercial_use": True, "self_host": True,
                       "sheet_commercial_use": True, "sheet_self_host": True}
        }

    def test_accept_only_auction_photos_and_matching_full_sheet(self):
        pub, private, binaries = normalize_lot(self.row, self.media)
        self.assertEqual(len(binaries), 2)
        self.assertEqual(pub["sheet_type"], "original_auction_sheet")
        self.assertEqual(pub["photo_context"], "original_auction_lot")
        self.assertEqual(pub["sale_status"], "reference_only")
        self.assertNotIn("sold_price", pub)
        self.assertTrue(pub["photos"][0].startswith("/assets/auction/approved/"))
        self.assertTrue(pub["auction_sheet"].startswith("/assets/auction/approved/"))
        self.assertEqual(private["license_evidence"], "test-license")

    def test_reject_street_showroom_and_other_nonauction_photo_context(self):
        for context in ("street", "showroom", "dealer", "stock", "warehouse", "port", ""):
            row = copy.deepcopy(self.row)
            row["photo_context"] = context
            with self.subTest(context=context), self.assertRaisesRegex(ValueError, "street/showroom"):
                normalize_lot(row, self.media)

    def test_reject_mismatched_sheet_photo_and_missing_sheet_license(self):
        cases = [
            ("photo_lot", lambda r: r["photo_evidence"][0].update({"lot": "999"})),
            ("photo_kind", lambda r: r["photo_evidence"][0].update({"capture_type": "street_photo"})),
            ("photo_proof", lambda r: r["photo_evidence"][0].update({"proof_reference": ""})),
            ("sheet_lot", lambda r: r["sheet_evidence"].update({"lot": "999"})),
            ("sheet_kind", lambda r: r["sheet_evidence"].update({"document_type": "damage_diagram"})),
            ("sheet_file", lambda r: r.update({"auction_sheet": "absent.jpg"})),
            ("sheet_license", lambda r: r["rights"].update({"sheet_commercial_use": False})),
            ("photo_license", lambda r: r["rights"].update({"commercial_use": False})),
            ("unverified_mileage", lambda r: r.pop("mileage_km")),
            ("unverified_description", lambda r: r.update({"description": ""}))
        ]
        for name, mutate in cases:
            row = copy.deepcopy(self.row)
            mutate(row)
            with self.subTest(name=name), self.assertRaises(ValueError):
                normalize_lot(row, self.media)

    def test_reference_lot_must_never_have_fabricated_sale_price(self):
        row = copy.deepcopy(self.row)
        row["sale_status"] = "verified_sold"
        with self.assertRaises(ValueError):
            normalize_lot(row, self.media)
        row.update({"sale_evidence_reference": "test-sale", "sold_date": "2026-05-12",
                    "currency": "KRW", "sold_price": 9700000})
        pub, _, _ = normalize_lot(row, self.media)
        self.assertEqual(pub["sold_price"], 9700000)

    def _prepare_target(self, pub, private, binaries):
        target = self.base / "render-public"
        target.mkdir()
        (target / "gallery.html").write_text((ROOT / "gallery.html").read_text(encoding="utf-8"),
                                              encoding="utf-8")
        source = json.loads((ROOT / "data/gallery-lots.json").read_text(encoding="utf-8"))
        (target / "data").mkdir()
        (target / "data/gallery-lots.json").write_text(json.dumps(source), encoding="utf-8")
        for item in source["lots"]:
            for src in (item["photos"][0], item["inspection_image"]):
                dest = target / src.lstrip("/")
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(b"test-only")
        for name, content, sha in binaries:
            dest = target / "assets" / "auction" / "approved" / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
        approved_path = self.base / "approved.json"
        approved_path.write_text(json.dumps({"lots": [pub]}), encoding="utf-8")
        rights_path = self.base / "rights.json"
        rights_path.write_text(json.dumps({"lots": [private]}), encoding="utf-8")
        return target, approved_path, rights_path

    def test_compiles_40_cards_with_one_licensed_korean_auction_lot(self):
        pub, private, binaries = normalize_lot(self.row, self.media)
        target, approved_path, rights_path = self._prepare_target(pub, private, binaries)
        result = compile_published_gallery(target, approved_path, rights_path)
        self.assertEqual(result["count"], 40)
        self.assertEqual(result["new"], 1)
        doc = json.loads((target / "data/gallery-lots.json").read_text(encoding="utf-8"))
        self.assertEqual(len(doc["lots"]), 40)
        new = doc["lots"][-1]
        self.assertEqual(new["market"], "south-korea")
        self.assertEqual(new["inspection_kind"], "Аукционный лист")
        self.assertEqual(new["status"], "reference_only")
        self.assertEqual(new["price_amount"], 0)
        html = (target / "gallery.html").read_text(encoding="utf-8")
        self.assertEqual(html.count('class="gallery-card"'), 40)
        self.assertIn("Все 40</button>", html)
        self.assertIn("Аукционный лист Hyundai Avante", html)
        self.assertIn("Цена продажи не подтверждена", html)
        self.assertNotIn("/assets/demo/", html)

    def test_compiler_refuses_missing_or_tampered_private_rights_ledger(self):
        pub, private, binaries = normalize_lot(self.row, self.media)
        target, approved_path, rights_path = self._prepare_target(pub, private, binaries)
        with self.assertRaisesRegex(RuntimeError, "ledger missing"):
            compile_published_gallery(target, approved_path, self.base / "missing.json")
        tampered = copy.deepcopy(private)
        tampered["photo_sha256"][0] = "bad-hash"
        rights_path.write_text(json.dumps({"lots": [tampered]}), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "altered photo"):
            compile_published_gallery(target, approved_path, rights_path)

    def test_compiler_refuses_any_entry_without_full_auction_sheet(self):
        pub, private, binaries = normalize_lot(self.row, self.media)
        target, approved_path, rights_path = self._prepare_target(pub, private, binaries)
        pub["sheet_type"] = "damage_diagram"
        approved_path.write_text(json.dumps({"lots": [pub]}), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "auction sheet not original"):
            compile_published_gallery(target, approved_path, rights_path)

    def test_500_hard_limit(self):
        pub, private, binaries = normalize_lot(self.row, self.media)
        target, approved_path, rights_path = self._prepare_target(pub, private, binaries)
        approved_path.write_text(json.dumps({"lots": [pub] * 462}), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "500"):
            compile_published_gallery(target, approved_path, rights_path)


if __name__ == "__main__":
    unittest.main()
