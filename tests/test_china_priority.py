"""Exact owner-approved China priority filters must not create cars or new photos."""
import json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ChinaPriority(unittest.TestCase):
 def test_exact_focus(self):
  p=json.loads((ROOT/"research/china-priority-20-2026-11-25.json").read_text())
  h=(ROOT/"china-order.html").read_text()
  groups=p["focus_groups"]
  self.assertEqual(len(groups),20)
  self.assertEqual(len({r["key"] for r in groups}),20)
  self.assertEqual(re.findall(r'data-focus="([^"]+)"',h),[r["key"] for r in groups])
  raw=re.search(r',map=(\{[^;]+?\}),labels=',h)
  self.assertIsNotNone(raw)
  m=json.loads(raw[1])
  expected={x["photo"]:r["key"] for r in groups for x in r["approved_archive_candidates"]}
  self.assertEqual(m,expected)
  allphotos=re.findall(r'<img\b[^>]*\bsrc="([^"]+)"',h)
  self.assertEqual(len(allphotos),529)
  self.assertTrue(set(m)<=set(allphotos))
  self.assertEqual(len(m),p["focus_candidate_count"])
  self.assertTrue(all(x["photo"] not in m for x in p["excluded_from_focus"]))
  self.assertIn('value="priority" selected',h)
  self.assertIn('Весь архив поставщиков',h)
