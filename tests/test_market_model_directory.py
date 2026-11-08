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

    def test_all_photo_previews_are_self_hosted_with_commercial_rights_and_attribution(self):
        js = (ROOT / "catalog-open-data.js").read_text(encoding="utf-8")
        manifest = json.loads((ROOT / "research" / "cc0-photo-provenance.json").read_text(encoding="utf-8"))
        for row in manifest["photos"]:
            with self.subTest(photo=row["file"]):
                self.assertTrue(
                    row["rights"] == "Creative Commons Zero 1.0 Universal (CC0)"
                    or re.fullmatch(r"CC BY(?:-SA)? (?:2\.0|2\.5|3\.0|4\.0)", row["rights"]),
                    row["rights"])
                if "CC0" not in row["rights"]:
                    self.assertIn("creativecommons.org/licenses/", row["license_evidence"])
                    self.assertTrue(row["author"].strip())
                    self.assertTrue(row["source_page"].startswith("https://commons.wikimedia.org/wiki/File:"))
                    credits = (ROOT / "photo-credits.html").read_text(encoding="utf-8")
                    self.assertIn(row["file"], credits)
                    self.assertIn(row["license_evidence"], credits)
                self.assertIn(row["file"], js)
                self.assertTrue(row["file"].startswith("/assets/demo/"))
                f = ROOT / row["file"].lstrip("/")
                self.assertTrue(f.is_file())
                self.assertGreater(f.stat().st_size, 30_000)
        self.assertGreaterEqual(len(manifest["photos"]), 20)
        # Fail the predeploy gate if the public catalog references an image that
        # is not rights-audited and physically self-hosted in the current tree.
        from_preview = set(re.findall(
            r'\["[^"]+\|[^"]+\|[^"]+","(/assets/demo/[^"]+\.webp)"\]', js
        ))
        tracked = {row["file"] for row in manifest["photos"]}
        self.assertEqual(len(tracked), len(manifest["photos"]))
        self.assertSetEqual(from_preview, tracked)


if __name__ == "__main__":
    unittest.main()
