"""Permanent PapAuto gate: NO generic street/model photographs, only exact auction lots."""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
IMAGE_SUFFIXES = {".webp", ".jpg", ".jpeg", ".png", ".gif"}


class AuctionOnlyImages(unittest.TestCase):
    def test_retired_galleries_and_downloaders_are_absent(self):
        forbidden = (
            "assets/demo",
            "assets/visual/lexus-dark-car-hero.webp",
            "assets/visual/papauto-lexus-light-hero.webp",
            "assets/auction/demo-cars-sprite.webp",
            "research/cc0-photo-provenance.json",
            "research/approved-cc0-vehicle-sources.json",
            "scripts/import_cc0_vehicle_images.py",
            "scripts/discover_and_expand_cc0_catalog.py",
            ".github/workflows/import-cc0-car-photos.yml",
            ".github/workflows/expand-cc0-car-directory.yml",
            ".github/workflows/import-korea-premium-media.yml",
            "premium-korea-media.js",
        )
        for name in forbidden:
            with self.subTest(name=name):
                self.assertFalse((ROOT / name).exists(), name)

    def test_all_vehicle_images_live_only_in_auction_dirs(self):
        photos = [p for p in (ROOT / "assets").rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES]
        self.assertGreaterEqual(len(photos), 80)
        for p in photos:
            relative=p.relative_to(ROOT).as_posix()
            self.assertTrue(
                relative.startswith("assets/auction/home/")
                or relative.startswith("assets/premium-auctions/"),
                f"NON-AUCTION IMAGE BLOCKED: {relative}"
            )

    def test_public_site_code_has_no_street_photo_asset_links(self):
        sources=list(ROOT.glob("*.html"))+list(ROOT.glob("*.js"))+list(ROOT.glob("*.css"))
        for p in sources:
            c=p.read_text(encoding="utf-8")
            with self.subTest(file=p.name):
                self.assertNotIn("/assets/demo/",c)
                self.assertNotIn("/assets/visual/lexus-dark-car-hero.webp",c)
                self.assertNotIn("/assets/visual/papauto-lexus-light-hero.webp",c)
                self.assertNotIn("imagebox.autowini.com/upload",c)

    def test_confirmed_auction_lots_only(self):
        data=json.loads((ROOT / "data/premium-real-auction-lots.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["lots"]),14)
        self.assertTrue(all(lot["market"] == "japan" for lot in data["lots"]))
        doc=(ROOT / "premium-japan-korea.html").read_text(encoding="utf-8")
        self.assertEqual(doc.count('class="real-card"'),14)
        self.assertNotIn('data-real-market="korea"',doc)
        self.assertNotIn('class="car" data-brand=',doc)
        self.assertIn('/assets/premium-auctions/bmw-x1-u11-2025-front.webp',doc)
        models=json.loads((ROOT / "data/papauto-expanded-45x3-2026.json").read_text(encoding="utf-8"))
        self.assertEqual(len(models["items"]),135)
        for market in ("japan","korea","china"):
            self.assertEqual(sum(i["market"]==market for i in models["items"]),45)
        for item in models["items"]:
            self.assertFalse(set(item).intersection({"photo","image","photo_source","image_url","auction_sheet"}))

    def test_builder_disallows_street_photo_imports(self):
        builder=(ROOT / "scripts/build_static_public.py").read_text(encoding="utf-8")
        self.assertIn("PAPAUTO_POLICY: assets/demo",builder)
        self.assertIn("assets/premium-auctions",builder)
        self.assertIn("assets/auction/home",builder)


if __name__ == "__main__":
    unittest.main()
