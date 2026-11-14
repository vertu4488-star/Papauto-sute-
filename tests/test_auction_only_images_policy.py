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
                or relative.startswith("assets/auction/approved/")
                or relative.startswith("assets/premium-auctions/")
                or relative == "assets/visual/papauto-thursday-approved-editorial-artwork-20261112.webp",
                f"NON-AUCTION IMAGE BLOCKED: {relative}"
            )

    def test_thursday_artwork_only_in_homepage_hero_not_auction_lots(self):
        """One explicitly user-approved marketing illustration, never sold as auction media."""
        art = "assets/visual/papauto-thursday-approved-editorial-artwork-20261112.webp"
        self.assertTrue((ROOT / art).is_file())
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertEqual(home.count('src="/' + art + '"'), 1)
        self.assertIn("рекламная иллюстрация, не аукционный лот", home)
        for name in ("gallery.html", "premium-japan-korea.html", "models-100.html"):
            self.assertNotIn("/" + art, (ROOT / name).read_text(encoding="utf-8"))

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
        self.assertEqual(len(data["lots"]),12)
        self.assertTrue(all(lot["market"] == "japan" for lot in data["lots"]))
        self.assertTrue(all(lot["inspection_kind"] == "Аукционный лист" for lot in data["lots"]))
        doc=(ROOT / "premium-japan-korea.html").read_text(encoding="utf-8")
        self.assertEqual(doc.count('class="real-card"'),12)
        self.assertNotIn('data-real-market="korea"',doc)
        self.assertNotIn('class="car" data-brand=',doc)
        self.assertIn('/assets/premium-auctions/bmw-x1-u11-2025-front.webp',doc)
        models=json.loads((ROOT / "data/papauto-expanded-45x3-2026.json").read_text(encoding="utf-8"))
        self.assertEqual(len(models["items"]),135)
        for market in ("japan","korea","china"):
            self.assertEqual(sum(i["market"]==market for i in models["items"]),45)
        for item in models["items"]:
            self.assertFalse(set(item).intersection({"photo","image","photo_source","image_url","auction_sheet"}))

    def test_cdn_retirement_list_replaces_every_deleted_street_image(self):
        manifest=json.loads((ROOT / "research/retired-non-auction-photo-paths-2026-11-12.json").read_text(encoding="utf-8"))
        paths=manifest["paths"]
        self.assertEqual(len(paths),519)
        self.assertEqual(len(set(paths)),519)
        self.assertEqual(sum(p.startswith("assets/demo/") for p in paths),507)
        for p in paths:
            self.assertFalse((ROOT / p).exists(),p)
        builder=(ROOT / "scripts/build_static_public.py").read_text(encoding="utf-8")
        self.assertIn("dst.write_bytes(TOMBSTONE)",builder)

    def test_rejected_outdoor_images_are_tombstoned_and_never_reach_release(self):
        from scripts.build_static_public import QUARANTINED_OUTDOOR_MEDIA, TOMBSTONE
        old_audi = {
            "assets/premium-auctions/audi-q2-2021-front.webp",
            "assets/premium-auctions/audi-q2-2021-rear.webp",
            "assets/premium-auctions/audi-q2-2021-diagram.webp",
            "assets/premium-auctions/audi-q3-2021-front.webp",
            "assets/premium-auctions/audi-q3-2021-rear.webp",
            "assets/premium-auctions/audi-q3-2021-diagram.webp",
        }
        newly_rejected = {
            "assets/auction/home/nissan-note-2021-227-photo-1.jpg",
            "assets/premium-auctions/mercedes-a180-2020-front.webp",
            "assets/premium-auctions/mercedes-a180-2020-rear.webp",
        }
        self.assertEqual(QUARANTINED_OUTDOOR_MEDIA, old_audi | newly_rejected)
        gallery=json.loads((ROOT / "data/gallery-lots.json").read_text(encoding="utf-8"))
        source_html=(ROOT / "gallery.html").read_text(encoding="utf-8")
        # Six historical Audi images are gone entirely; two newer records stay
        # in internal source control for provenance, not in the published site.
        for rel in old_audi:
            self.assertNotIn("/" + rel, source_html)
            self.assertFalse(any("/" + rel in json.dumps(lot) for lot in gallery["lots"]))
        self.assertEqual(gallery["lot_count"], 37)
        for rel in newly_rejected:
            self.assertTrue(any("/" + rel in json.dumps(lot) for lot in gallery["lots"]))
        export=ROOT / "render-public"
        if export.is_dir():
            for rel in QUARANTINED_OUTDOOR_MEDIA:
                self.assertEqual((export / rel).read_bytes(), TOMBSTONE)
            pub_html=(export / "gallery.html").read_text(encoding="utf-8")
            pub=json.loads((export / "data/gallery-lots.json").read_text(encoding="utf-8"))
            self.assertEqual(pub["lot_count"], 35)
            for rel in QUARANTINED_OUTDOOR_MEDIA:
                self.assertNotIn("/" + rel, pub_html)
                self.assertFalse(any("/" + rel in json.dumps(lot) for lot in pub["lots"]))
            for rejected in ("nissan-note-2021-227", "mercedes-a180-2020"):
                self.assertFalse(any(lot["id"] == rejected for lot in pub["lots"]))

    def test_builder_disallows_street_photo_imports(self):
        builder=(ROOT / "scripts/build_static_public.py").read_text(encoding="utf-8")
        self.assertIn("PAPAUTO_POLICY: assets/demo",builder)
        self.assertIn("assets/premium-auctions",builder)
        self.assertIn("assets/auction/home",builder)


if __name__ == "__main__":
    unittest.main()
