"""Regression gate: quarantined outdoor auction shots never reach customer build."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from scripts.compile_auction_gallery import (
    compile_published_gallery, QUARANTINED_OUTDOOR_LOTS,
)
from scripts.build_static_public import QUARANTINED_OUTDOOR_MEDIA

ROOT = Path(__file__).resolve().parents[1]
REJECTED = {"nissan-note-2021-227", "mercedes-a180-2020"}
BAD_PHOTOS = {
    "assets/auction/home/nissan-note-2021-227-photo-1.jpg",
    "assets/premium-auctions/mercedes-a180-2020-front.webp",
    "assets/premium-auctions/mercedes-a180-2020-rear.webp",
}


class StreetPhotoPublicationGate(unittest.TestCase):
    def test_exclusion_and_tombstone_policies(self):
        self.assertEqual(set(QUARANTINED_OUTDOOR_LOTS), REJECTED)
        self.assertTrue(BAD_PHOTOS.issubset(QUARANTINED_OUTDOOR_MEDIA))
        src = json.loads((ROOT / "data/gallery-lots.json").read_text(encoding="utf-8"))
        self.assertEqual(src["lot_count"], 37)  # provenance preserved
        self.assertTrue(REJECTED.issubset({r["id"] for r in src["lots"]}))

    def test_generated_customer_gallery_has_35_indoor_cover_lots(self):
        src = json.loads((ROOT / "data/gallery-lots.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as td:
            dest = Path(td)
            (dest / "data").mkdir(parents=True)
            shutil.copy2(ROOT / "data/gallery-lots.json", dest / "data/gallery-lots.json")
            shutil.copy2(ROOT / "gallery.html", dest / "gallery.html")
            for lot in src["lots"]:
                if lot["id"] in REJECTED:
                    continue
                for url in lot["photos"] + [lot["inspection_image"]]:
                    from_path = ROOT / url.lstrip("/")
                    if not from_path.is_file():
                        continue  # optional extra angles are not required
                    to_path = dest / url.lstrip("/")
                    to_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(from_path, to_path)
            report = compile_published_gallery(dest)
            self.assertEqual(report["count"], 35)
            self.assertEqual(report["new"], 0)
            self.assertEqual(report["detail_pages"], 35)
            public = json.loads((dest / "data/gallery-lots.json").read_text(encoding="utf-8"))
            self.assertEqual(public["lot_count"], 35)
            self.assertEqual(len(public["lots"]), 35)
            self.assertFalse(REJECTED & {r["id"] for r in public["lots"]})
            html = (dest / "gallery.html").read_text(encoding="utf-8")
            self.assertEqual(html.count('class="gallery-card"'), 35)
            for lot_id in REJECTED:
                self.assertNotIn('id="gallery-lot-' + lot_id + '"', html)
                self.assertNotIn('"id":"' + lot_id + '"', html)
                self.assertFalse((dest / "lots" / (lot_id + ".html")).exists())
            for bad_photo in BAD_PHOTOS:
                self.assertNotIn(bad_photo, html)
                self.assertNotIn(bad_photo, json.dumps(public, ensure_ascii=False))
            self.assertTrue((dest / "lots" / "honda-fit-2021-10355.html").is_file())

if __name__ == "__main__":
    unittest.main()
