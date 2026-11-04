import json,unittest
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
class Signals(HTMLParser):
    def __init__(self,text):
        super().__init__();self.canon=[];self.desc=[];self.h1=0;self.titles=0;self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='link' and a.get('rel')=='canonical':self.canon.append(a['href'])
        if tag=='meta' and a.get('name')=='description':self.desc.append(a['content'])
        if tag=='h1':self.h1+=1
        if tag=='title':self.titles+=1
class SEOTests(unittest.TestCase):
    def test_sitemap_pages_have_matching_metadata(self):
        urls=[el.text for el in ET.parse(ROOT/'sitemap.xml').iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        self.assertEqual(len(urls),len(set(urls)))
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(urlsplit(url).netloc,'www.papauto.ru')
                path=urlsplit(url).path.lstrip('/') or 'index.html'
                text=(ROOT/path).read_text();s=Signals(text)
                self.assertEqual(s.canon,[url]);self.assertEqual(s.h1,1);self.assertEqual(s.titles,1)
                self.assertEqual(len(s.desc),1);self.assertTrue(s.desc[0]);self.assertNotIn('noindex',text)
    def test_buyer_page_targets_exist(self):
        for page in json.loads((ROOT/'content/buyer-pages.json').read_text()):
            for section in page['sections']:
                if 'link' in section:
                    path=urlsplit(section['link']).path.lstrip('/') or 'index.html'
                    self.assertTrue((ROOT/path).is_file(),path)
