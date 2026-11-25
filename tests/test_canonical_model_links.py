import unittest
from scripts.canonical_model_links import MODEL_REDIRECTS, canonical_href, rewrite_html

class CanonicalNavigationTest(unittest.TestCase):
    def test_exact_legacy_routes(self):
        self.assertEqual(len(MODEL_REDIRECTS), 15)
        for old, new in MODEL_REDIRECTS.items():
            self.assertEqual(canonical_href(old, "/index.html"), new)
            self.assertEqual(canonical_href("https://www.papauto.ru"+old+"?a=1#b", "/index.html"), "https://papauto.ru"+new+"?a=1#b")
            self.assertEqual(canonical_href("../"+old[1:], "/models/sample.html"), new)
            self.assertEqual(canonical_href("https://example.org"+old, "/index.html"), "https://example.org"+old)
            self.assertEqual(canonical_href(new, "/index.html"), new)
    def test_only_href(self):
        html = '<a href="/honda-fit-japan.html">Fit</a><img src="/honda-fit-japan.html">'
        self.assertEqual(rewrite_html(html, "/index.html"), '<a href="/models/japan-honda-fit.html">Fit</a><img src="/honda-fit-japan.html">')
