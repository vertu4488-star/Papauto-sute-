"""Regression guard for PapAuto's isolated GitHub Pages access tests."""
import ast
from pathlib import Path
import unittest


class GithubPagesCorsTest(unittest.TestCase):
    def test_allowed_origins_keep_preview_and_avoid_wildcard(self):
        source = (Path(__file__).resolve().parents[1] / "api.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        matches = [
            stmt.value for stmt in tree.body
            if isinstance(stmt, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "ALLOWED_SITE_ORIGINS"
                    for target in stmt.targets)
        ]
        self.assertEqual(1, len(matches))
        allowed = ast.literal_eval(matches[0])
        self.assertIn("https://papauto.ru", allowed)
        self.assertIn("https://vertu4488-star.github.io", allowed)
        self.assertNotIn("*", allowed)
        self.assertTrue(all(url.startswith("https://") for url in allowed))


    def test_frontend_uses_own_api_hostname_not_render_directly(self):
        config = (Path(__file__).resolve().parents[1] / "site-config.js").read_text(encoding="utf-8")
        self.assertIn('apiBaseUrl:"https://api.papauto.ru"', config)
        self.assertNotIn('apiBaseUrl:"https://papauto-leads.onrender.com"', config)



if __name__ == "__main__":
    unittest.main()
