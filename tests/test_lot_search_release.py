"""Search release must match the screened catalogue, never quarantined pages."""
import html
import json
import re
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

class LotSearchRelease(unittest.TestCase):
    def test_released_lots_have_unique_canonicals_and_sitemap_entries(self):
        root = Path(__file__).resolve().parents[1] / 'render-public'
        if not root.exists():
            self.skipTest('Build the static public bundle first')
        lots = json.loads((root / 'data/gallery-lots.json').read_text())['lots']
        main_urls = [e.text for e in ET.parse(root / 'sitemap.xml').iter() if e.tag.endswith('}loc')]
        lot_map = ET.parse(root / 'sitemap-lots.xml')
        lot_urls = [e.text for e in lot_map.iter() if e.tag.endswith('}loc')]
        lot_lastmods = [e.text for e in lot_map.iter() if e.tag.endswith('}lastmod')]
        self.assertEqual(len(lot_lastmods), len(lots))
        image_ns = '{http://www.google.com/schemas/sitemap-image/1.1}'
        photo_urls = [e.text for e in lot_map.iter() if e.tag == image_ns + 'loc']
        self.assertEqual(len(photo_urls), len(lots))
        self.assertTrue(all(p and p.startswith('https://papauto.ru/assets/') for p in photo_urls))
        self.assertTrue(all(re.fullmatch(r'20\d{2}-\d{2}-\d{2}', d or '') for d in lot_lastmods))
        self.assertEqual(len(lot_urls), len(set(lot_urls)))
        self.assertIn('https://papauto.ru/auction-lot-index.html', main_urls)
        self.assertNotIn('https://papauto.ru/auction-lot-index.html', lot_urls)
        directory = (root / 'auction-lot-index.html').read_text()
        self.assertIn(f'Количество опубликованных аукционных примеров: {len(lots)}', directory)
        self.assertIn(f'Все аукционные карточки ({len(lots)})', (root / 'gallery.html').read_text())
        for lot in lots:
            path = '/lots/' + lot['id'] + '.html'
            page = (root / path.lstrip('/')).read_text()
            title = re.search(r'<title>([^<]+)</title>', page)
            description = re.search(r'<meta name="description" content="([^"]+)"', page)
            self.assertIsNotNone(title, path)
            self.assertIsNotNone(description, path)
            self.assertLessEqual(len(html.unescape(title.group(1))), 60, path)
            self.assertLessEqual(len(html.unescape(description.group(1))), 160, path)
            self.assertIn('content="index,follow"', page)
            self.assertIn('rel="canonical" href="https://papauto.ru'+path+'"', page)
            breadcrumbs = re.findall(r'<script type="application/ld\+json">([^<]+)</script>', page)
            self.assertTrue(any(json.loads(b).get('@type') == 'BreadcrumbList' for b in breadcrumbs), path)
            self.assertEqual(lot_urls.count('https://papauto.ru'+path), 1)
            self.assertNotIn('https://papauto.ru'+path, main_urls)
            self.assertIn('href="'+path+'"', directory)
            self.assertIn('Архив', directory)
            self.assertNotIn('/calculator.html', page)
        for rejected in ['nissan-note-2021-227', 'mercedes-a180-2020']:
            self.assertNotIn('https://papauto.ru/lots/'+rejected+'.html', main_urls)
            self.assertNotIn('https://papauto.ru/lots/'+rejected+'.html', lot_urls)
