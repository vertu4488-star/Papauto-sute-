"""Search release must match the screened catalogue, never quarantined pages."""
import json
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

class LotSearchRelease(unittest.TestCase):
    def test_released_lots_have_unique_canonicals_and_sitemap_entries(self):
        root = Path(__file__).resolve().parents[1] / 'render-public'
        if not root.exists():
            self.skipTest('Build the static public bundle first')
        lots = json.loads((root / 'data/gallery-lots.json').read_text())['lots']
        urls = [e.text for e in ET.parse(root / 'sitemap.xml').iter() if e.tag.endswith('}loc')]
        directory = (root / 'auction-lot-index.html').read_text()
        for lot in lots:
            path = '/lots/' + lot['id'] + '.html'
            page = (root / path.lstrip('/')).read_text()
            self.assertIn('content="index,follow"', page)
            self.assertIn('rel="canonical" href="https://papauto.ru'+path+'"', page)
            self.assertEqual(urls.count('https://papauto.ru'+path), 1)
            self.assertIn('href="'+path+'"', directory)
            self.assertIn('Архив', directory)
            self.assertNotIn('/calculator.html', page)
        for rejected in ['nissan-note-2021-227', 'mercedes-a180-2020']:
            self.assertNotIn('https://papauto.ru/lots/'+rejected+'.html', urls)
