"""PapAuto public model directory: no duplicates, leakage or misleading claims."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def model_catalog_parts():
    js = (ROOT / "vehicle-catalogue.js").read_text(encoding="utf-8")
    base = re.search(r"const catalog = (\{.*?\});\s*// PAPAUTO_JTECO_MODEL_EXPANSION", js, re.S)
    added = re.search(r"const directoryExpansion = (\{.*?\});\s*for \(const region", js, re.S)
    if not base or not added:
        raise AssertionError("Catalog expansion marker or inline source data missing")
    initial = json.loads(re.sub(r"\b(japan|china)(?=\s*:)", r'"\1"', base.group(1)))
    expansion = json.loads(added.group(1))
    return initial, expansion


class MarketModelDirectory(unittest.TestCase):
    def test_real_market_structure_and_unique_names(self):
        initial, expansion = model_catalog_parts()
        self.assertEqual(set(initial), {"japan", "south-korea", "china"})
        self.assertEqual(set(expansion), set(initial))
        desired_min = {"japan": 180, "south-korea": 120, "china": 195}
        for region, base in initial.items():
            with self.subTest(market=region):
                rows = base + expansion[region]
                self.assertTrue(all(len(x) == 3 and all(isinstance(v, str) and v.strip() for v in x) for x in rows))
                keys = {(x[0].casefold(), x[1].casefold()) for x in rows}
                self.assertGreaterEqual(len(keys), desired_min[region])
                self.assertFalse(any("<" in v or ">" in v or "http" in v.lower() for r in rows for v in r))
        self.assertGreaterEqual(sum(len({(a.casefold(), b.casefold()) for a, b, _ in initial[k] + expansion[k]}) for k in initial), 510)

    def test_no_outbound_dealer_links_in_public_catalog_renderer(self):
        js = (ROOT / "catalog-open-data.js").read_text(encoding="utf-8")
        for domain in ("jteco.ru", "drom.ru", "plc.auction", "auto.ru", "commons.wikimedia.org"):
            self.assertNotIn(domain, js)
        self.assertIn('encodeURIComponent(r.brand+" "+r.model)', js)
        self.assertIn('const make = by("makeFilter")', js)
        page = (ROOT / "catalog.html").read_text(encoding="utf-8")
        self.assertIn('id="makeFilter"', page)
        self.assertLess(page.index('id="modelQuery"'), page.index('aria-label="Популярные модели"'))
        self.assertNotIn("Карточки реальных аукционных лотов с фотографиями", page)

    def test_all_photo_previews_are_self_hosted_cc0_with_evidence(self):
        js = (ROOT / "catalog-open-data.js").read_text(encoding="utf-8")
        manifest = json.loads((ROOT / "research" / "cc0-photo-provenance.json").read_text(encoding="utf-8"))
        for row in manifest["photos"]:
            with self.subTest(photo=row["file"]):
                self.assertEqual(row["rights"], "Creative Commons Zero 1.0 Universal (CC0)")
                self.assertIn(row["file"], js)
                self.assertTrue(row["file"].startswith("/assets/demo/"))
                f = ROOT / row["file"].lstrip("/")
                self.assertTrue(f.is_file())
                self.assertGreater(f.stat().st_size, 30_000)
        self.assertGreaterEqual(len(manifest["photos"]), 4)


if __name__ == "__main__":
    unittest.main()
