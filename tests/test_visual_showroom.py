"""Only verified auction-result data may appear as car cards on the homepage."""
from html.parser import HTMLParser
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class AuctionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lots=0
        self.images=0
        self.outbound=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="article" and "pa-real-lot" in a.get("class","").split():
            self.lots+=1
        if tag=="img":
            self.images+=1
        if tag=="a":
            self.outbound.append(a.get("href",""))

class AuctionHomepage(unittest.TestCase):
    def test_homepage_shows_sourced_lots_not_street_photos(self):
        html=(ROOT/"index.html").read_text(encoding="utf-8")
        start=html.index('<section class="pa-vitrine')
        end=html.index("</section>",start)+len("</section>")
        section=html[start:end]
        p=AuctionParser()
        p.feed(section)
        self.assertEqual(p.lots,25)
        self.assertEqual(p.images,87,"Every lot must show original photos and its sheet")
        self.assertEqual(section.count('class="pa-real-media"'),25)
        self.assertEqual(section.count('class="pa-auction-more"'),1)
        self.assertIn("Показать ещё 17 аукционных лотов",section)
        featured, rest = section.split('<details class="pa-auction-more">',1)
        self.assertEqual(featured.count('class="pa-real-lot"'),8)
        self.assertEqual(rest.count('class="pa-real-lot"'),17)
        self.assertEqual(section.count('class="pa-real-sheet"'),25)
        self.assertTrue(all(src.startswith("/assets/auction/home/") for src in __import__("re").findall(r'<img[^>]+src="([^"]+)"',section)))
        self.assertNotIn("pa-featured-card",section)
        self.assertNotIn("pa-car-photo",section)
        self.assertIn("Фактическая цена продажи",section)
        self.assertEqual(section.count('class="pa-sale-stats"'),25)
        self.assertIn("Пробег",section)
        self.assertIn("Оценка",section)
        self.assertIn("Аукцион",section)
        self.assertIn("Все 25 автомобилей",section)
        self.assertTrue(all(u.startswith("/") for u in p.outbound))
        self.assertNotIn("atp-auto",section.lower())
        self.assertNotIn("drom",section.lower())
        self.assertIn('/home-auction-real.css',html)
    def test_evidence_is_outside_public_build(self):
        path=ROOT/"research"/"home-auction-examples-2026-11-12.json"
        doc=json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(doc["lots"]),8)
        for lot in doc["lots"]:
            self.assertTrue(lot["origin"].startswith("https://"))
            self.assertGreater(lot["mileage"],0)
            self.assertGreater(lot["price"],0)
            self.assertTrue(lot["lot"] and lot["auction"])
        build=(ROOT/"scripts"/"build_static_public.py").read_text(encoding="utf-8")
        self.assertIn('"research"',build)
        self.assertIn('"/assets/visual/fallback-vehicle.svg"',build)
        self.assertIn('PAPAUTO_POLICY: assets/demo',build)

if __name__=="__main__":
    unittest.main()
