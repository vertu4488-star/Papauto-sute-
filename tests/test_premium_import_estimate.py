"""The premium estimate is sourced from verified sold lots, not invented tariffs."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
class ImportCostTests(unittest.TestCase):
    def test_source_lots_and_private_rates(self):
        js=(ROOT/"premium-import-estimate.js").read_text(encoding="utf-8")
        self.assertIn('/data/premium-real-auction-lots.json',js)
        self.assertIn('status==="sold"',js)
        self.assertIn("dutyEur",js)
        self.assertIn("utilRub",js)
        self.assertIn("export_restricted",js)
        self.assertNotIn("api/leads",js)
        self.assertNotIn("145000",js)
        self.assertNotIn("5200",js)
        self.assertEqual(len(json.loads((ROOT/"data/premium-real-auction-lots.json").read_text(encoding="utf-8"))["lots"]),12)
    def test_page_has_local_assets_and_calculator(self):
        html=(ROOT/"premium-japan-korea.html").read_text(encoding="utf-8")
        self.assertIn('id="premiumImportCost"',html)
        self.assertIn('id="import-estimate"',html)
        self.assertIn('/premium-import-estimate.js',html)
        self.assertIn('/premium-import-estimate.css',html)
if __name__=="__main__":unittest.main()
