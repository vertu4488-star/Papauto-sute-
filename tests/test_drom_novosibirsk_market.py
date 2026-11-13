"""Safe Drom Novosibirsk market reading must not leak competitor photos into PapAuto."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"research/drom-novosibirsk-991-no-rf-2026-11-13.json"
class DromLocalMarketAudit(unittest.TestCase):
  def test_live_count_and_sample_scope(self):
    x=json.loads(SOURCE.read_text(encoding="utf-8"))
    self.assertEqual(x["result_count_in_live_browser"],991)
    self.assertEqual(len(x["listings_sample"]),40)
    self.assertEqual(x["listing_count_sampled"],40)
    self.assertEqual(len(x["priorities"]),32)
    self.assertEqual(len({r["rank"] for r in x["priorities"]}),32)
    self.assertTrue(all(x["region"]=="Новосибирск (город, не область)" for _ in [1]))
  def test_all_prepared_existing_gallery_cards_refer_to_real_lots(self):
    x=json.loads(SOURCE.read_text(encoding="utf-8"))
    g=json.loads((ROOT/"data/gallery-lots.json").read_text(encoding="utf-8"))
    known={l["id"] for l in g["lots"]}
    for row in x["priorities"]:
      a=row["existing_papauto_auction_example"]
      if a:
        self.assertIn(a["id"],known)
        self.assertFalse(a["image_setting_visually_rechecked"])
        self.assertFalse(a["image_rights_confirmed"])
    self.assertEqual(x["new_published_lots"],0)
    self.assertEqual(len(g["lots"]),37)
  def test_no_drom_photo_links_or_articles_inserted_into_public_gallery(self):
    html=(ROOT/"gallery.html").read_text(encoding="utf-8")
    self.assertNotIn("r1.drom.ru",html)
    self.assertNotIn("r2.drom.ru",html)
    self.assertNotIn("auto.drom.ru",html)
    self.assertEqual(html.count('class="gallery-card"'),37)
if __name__=="__main__":
  unittest.main()
