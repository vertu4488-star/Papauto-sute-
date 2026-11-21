"""PapAuto warm palette gate — prevents any blue/cool CSS from reappearing.

The owner's design requirement applies to every page, not only the hero.
Audit local root CSS (including premium cards, gallery, modal, mobile and lots)
and all HTML emitted by the public static builder.
"""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/"render-public"
HEX=re.compile(r"#[\da-fA-F]{3,8}\b")
STYLE=re.compile(r"<style\b[^>]*>[\s\S]*?</style>",re.I)
INLINE=re.compile(r"""\bstyle=(['"])(.*?)\1""",re.I|re.S)


def cold(hexcolor):
    h=hexcolor[1:]
    if len(h) not in (3,4,6,8):
        return False
    if len(h) in (3,4):
        h="".join(c+c for c in h)
    r,g,b=(int(h[x:x+2],16) for x in (0,2,4))
    return b>r+5 and b>=g-12


class PapautoWarmPalette(unittest.TestCase):
    def test_all_root_css_no_cold_color_literals(self):
        offenders=[]
        css=list(ROOT.glob("*.css"))
        self.assertGreaterEqual(len(css),30)
        for file in css:
            for color in HEX.findall(file.read_text(encoding="utf8")):
                if cold(color):
                    offenders.append((file.name,color))
        self.assertFalse(offenders,"Cold CSS remains: "+str(offenders[:25]))

    def test_all_public_html_uses_final_unified_warm_skin(self):
        if not PUBLIC.exists():
            self.skipTest("Build output not yet generated")
        sample=["index.html","gallery.html","catalog.html",
                "premium-japan-korea.html","podbor.html",
                "japan.html","korea.html","china.html"]
        for name in sample:
            text=(PUBLIC/name).read_text(encoding="utf8")
            with self.subTest(page=name):
                self.assertEqual(text.count('papauto-warm-interior.css'),1)
                self.assertIn("20261115-all-site-v4",text)
                if name=="index.html":
                    self.assertIn('class="pa-thursday-home"',text)
                else:
                    self.assertIn('class="papauto-warm-interior',text)

    def test_inline_css_is_not_blue_in_published_pages(self):
        if not PUBLIC.exists():
            self.skipTest("Build output not yet generated")
        exceptions=[]
        for path in PUBLIC.glob("*.html"):
            text=path.read_text(encoding="utf8")
            blocks=STYLE.findall(text)
            blocks += [m.group(2) for m in INLINE.finditer(text)]
            for block in blocks:
                for color in HEX.findall(block):
                    if cold(color):
                        exceptions.append((path.name,color))
        self.assertFalse(exceptions,"Cool inline CSS remains: "+str(exceptions[:25]))

    def test_static_auction_sheet_protection_unchanged(self):
        if not PUBLIC.exists():
            self.skipTest("Build output not yet generated")
        import json
        lots=json.loads((PUBLIC/"data/gallery-lots.json").read_text(encoding="utf8"))
        self.assertEqual(lots["lot_count"],639)
        for lot in lots["lots"]:
            self.assertTrue(lot["photos"])
            self.assertTrue(lot["inspection_image"].startswith("/assets/"))
            self.assertTrue((PUBLIC/lot["inspection_image"].lstrip("/")).is_file())


if __name__=="__main__":
    unittest.main()
