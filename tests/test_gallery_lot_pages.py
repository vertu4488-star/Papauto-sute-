"""Buyer-facing full-sheet detail pages: 37 genuine lots, no source links and no SEO pushes."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from scripts.generate_auction_lot_pages import generate, render_lot

ROOT=Path(__file__).resolve().parents[1]
GALLERY=json.loads((ROOT/"data/gallery-lots.json").read_text(encoding="utf-8"))


class AuctionLotDetails(unittest.TestCase):
    def test_generates_37_real_lot_pages_with_photo_sheet_description_and_noindex(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            report=generate(GALLERY,root,ROOT)
            self.assertEqual(report["detail_pages"],37)
            pages=list((root/"lots").glob("*.html"))
            self.assertEqual(len(pages),37)
            for lot in GALLERY["lots"]:
                page=(root/"lots"/(lot["id"]+".html")).read_text(encoding="utf-8")
                self.assertIn('content="noindex,follow"',page)
                self.assertIn(lot["model"],page)
                self.assertIn(lot["description"].split(". ")[0],page)
                self.assertIn(lot["inspection_image"],page)
                self.assertIn(lot["photos"][0],page)
                self.assertIn('href="/podbor.html?similar=',page)
                self.assertNotIn('href="https://',page)
                self.assertNotIn('/assets/demo/',page)
                self.assertNotIn('/assets/visual/',page)
                self.assertNotIn('class="gallery-missing-media"',page)

    def test_rejects_diagram_only_and_external_photos(self):
        example=GALLERY["lots"][0]
        bad=copy.deepcopy(example)
        bad["inspection_kind"]="Схема повреждений"
        with self.assertRaisesRegex(RuntimeError,"auction sheet"):
            render_lot(bad,ROOT)
        bad=copy.deepcopy(example)
        bad["photos"]=["https://seller.example/stock.jpg"]
        with self.assertRaisesRegex(RuntimeError,"approved local auction"):
            render_lot(bad,ROOT)

    def test_rejects_bad_description_and_unverified_sold_price(self):
        bad=copy.deepcopy(GALLERY["lots"][0]);bad["description"]=""
        with self.assertRaisesRegex(RuntimeError,"description"):
            render_lot(bad,ROOT)
        bad=copy.deepcopy(GALLERY["lots"][0]);bad["price_jpy"]=0
        with self.assertRaisesRegex(RuntimeError,"unsubstantiated"):
            render_lot(bad,ROOT)

if __name__=="__main__":
    unittest.main()
