"""Regression: CSS selectors must not be counted as model entries."""
import json
from pathlib import Path
import tempfile
import unittest
from scripts.enrich_model_directory import render_directory

class DirectoryRegression(unittest.TestCase):
    def test_css_selector_and_mixed_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data").mkdir()
            (root / "models").mkdir()
            (root / "assets").mkdir()
            (root / "assets/photo.jpg").write_bytes(b"x" * 101)
            items = []
            reports = []
            for i in range(135):
                ident = f"model-{i}"
                items.append(dict(id=ident, market=("japan", "korea", "china")[i % 3], brand="Test", model=str(i)))
                reports.append(dict(model_id=ident, auction_matches=int(i == 0)))
                card = '<article class="pa-model-lot"><img src="/assets/photo.jpg"><h3>Exact example</h3></article>' if i == 0 else ""
                (root / "models" / (ident + ".html")).write_text("<html><head></head><body><h1>Model</h1>" + card + "</body></html>")
            (root / "data/papauto-expanded-45x3-2026.json").write_text(json.dumps({"items": items}))
            (root / "models-135.html").write_text('<html><head><link rel="canonical" href="https://papauto.ru/models-135.html"></head><body><main>Old</main></body></html>')
            render_directory(root, {"models": reports})
            html = (root / "models-135.html").read_text()
            self.assertIn("[data-pa-directory-entry][hidden]", html)
            self.assertEqual(html.count(" data-pa-directory-entry "), 135)
            self.assertEqual(html.count('<article class="pa-directory-card"'), 1)
            self.assertEqual((root / "models-100.html").read_text(), html)

    def test_legacy_source_has_canonical_directory(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "models-100.html").read_text()
        self.assertIn('rel="canonical" href="https://papauto.ru/models-135.html"', html)
        self.assertNotIn('rel="canonical" href="https://papauto.ru/models-100.html"', html)
