"""Auction-only unified 37-lot gallery with image-to-lot evidence, no invented listings."""
from pathlib import Path
import json
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
class AuctionGalleryTests(unittest.TestCase):
    def test_public_unified_catalog_matches_source_exact_lots(self):
        data=json.loads((ROOT/"data/gallery-lots.json").read_text(encoding="utf-8"))
        source=json.loads((ROOT/"research/home-8-exact-lot-photo-sheet-references-2026-11-12.json").read_text(encoding="utf-8"))
        premium=json.loads((ROOT/"data/premium-real-auction-lots.json").read_text(encoding="utf-8"))
        lots=data["lots"]
        self.assertEqual(data["lot_count"],37)
        self.assertEqual(len(lots),37)
        self.assertEqual(len({l["id"] for l in lots}),37)
        self.assertEqual(len([l for l in lots if l["origin"]=="home"]),25)
        self.assertEqual(len([l for l in lots if l["origin"]=="premium"]),12)
        self.assertTrue(all(len(l.get("description",""))>=110 for l in lots),
                        "Each auction card must include a meaningful source-backed description")
        self.assertEqual(len({l["description"] for l in lots}),37,
                         "Descriptions must correspond to distinct lot records")
        self.assertTrue(all(l["description"].find(l["lot_number"])>=0 for l in lots))
        self.assertEqual(len([l for l in lots if l.get("engine_cc")]),12,
                         "Engine sizes must be published only when listed in the premium source")

        src_home={r["slug"]:r for r in source["records"]}
        src_premium={r["id"]:r for r in premium["lots"]}
        for lot in lots:
            self.assertEqual(lot["inspection_kind"],"Аукционный лист")
            self.assertEqual(lot["market"],"japan")
            self.assertGreater(lot["price_jpy"],0)
            self.assertFalse(lot["rights_confirmed"],"Licensing must never be fabricated")
            self.assertRegex(lot["photos"][0],r"^/assets/(auction/home|premium-auctions)/[a-z0-9-]+\.(jpg|webp)$")
            self.assertTrue((ROOT/lot["photos"][0].lstrip("/")).is_file(),lot["id"])
            self.assertTrue((ROOT/lot["inspection_image"].lstrip("/")).is_file(),lot["id"])
            if lot["origin"]=="home":
                ref=src_home[lot["id"]]
                self.assertEqual(lot["price_jpy"],ref["sale_price_jpy"])
                self.assertEqual(lot["lot_number"],str(ref["lot_number"]))
                self.assertEqual(lot["mileage_km"],ref["mileage_km"])
                self.assertEqual(len(lot["photos"]),len(ref["auction_photos"]))
            else:
                ref=src_premium[lot["id"]]
                self.assertEqual(lot["price_jpy"],int(re.sub(r"\D","",ref["price_jpy"])))
                self.assertEqual(lot["photos"],ref["photos"])
                self.assertEqual(lot["inspection_kind"],ref["inspection_kind"])
    def test_page_uses_self_hosted_photos_and_no_competitor_links(self):
        page=(ROOT/"gallery.html").read_text(encoding="utf-8")
        js=(ROOT/"gallery.js").read_text(encoding="utf-8")
        self.assertIn('rel="canonical" href="https://papauto.ru/gallery.html"',page)
        self.assertIn('id="gallery-grid"',page)
        self.assertIn('id="gallery-bootstrap"',page)
        self.assertEqual(page.count('class="gallery-card"'),37)
        self.assertEqual(page.count('class="gallery-description"'),37)
        self.assertIn('element("p","gallery-description",lot.description)',js)

        self.assertNotIn('Подготавливаем аукционную галерею…',page)
        self.assertNotIn('fetch("/data/gallery-lots.json"',js)
        self.assertIn("object-fit:contain",(ROOT/"gallery.css").read_text(encoding="utf-8"))
        self.assertIn("data-gallery-category",page)
        self.assertIn('id="gallery-market-filter"',page)
        self.assertIn("a.market.localeCompare(b.market)",js,
                      "Never compare JPY, KRW and CNY amounts directly")
        self.assertIn('href="/podbor.html"',page)
        self.assertIn('JSON.parse(bootstrap.textContent)',js)
        self.assertIn("Gallery published:",(ROOT/"scripts/build_static_public.py").read_text(encoding="utf-8"))
        self.assertNotIn("https://",js)
        self.assertNotIn("/assets/demo/",js)
        self.assertIn("https://papauto.ru/gallery.html",(ROOT/"sitemap.xml").read_text(encoding="utf-8"))
        self.assertIn('href="/gallery.html"',(ROOT/"index.html").read_text(encoding="utf-8"))
if __name__=="__main__":unittest.main()
