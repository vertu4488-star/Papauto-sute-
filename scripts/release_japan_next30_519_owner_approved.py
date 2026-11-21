"""Publish exactly the 30 user-approved Japanese source-backed archive cards 489 -> 519.

Runs only in GitHub Actions with the two frozen source artifact directories. Exactly
matches PDF and ZIP approval hashes; no third-party commercial license implied.
"""
from pathlib import Path
from io import BytesIO
import json, hashlib, re
from PIL import Image

ROOT=Path(".")
SPEC={
 "wave3":("14691820564","9bd14bac931dbacfb3fc2578cf52816ce9fd5a2b6c666d04eff9ec42c01ebdc2"),
 "b6":("14641252098","fe2fb3d5f95195e9fd084dc72a5ad4f349dd9f100195bf1e5c5d13bfb1c58838")}
def sha(b):return hashlib.sha256(b).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def norm(s):return re.sub("[^a-z0-9]","",str(s).lower())
def key(r):return (norm(r["auction"]),str(r.get("auction_date") or r.get("date") or "")[:10],str(r.get("lot") or r.get("lot_number") or "").lstrip("0"))
def sub(path,a,b):
 p=Path(path);t=p.read_text(encoding="utf-8")
 assert t.count(a)==1,(path,a,t.count(a))
 p.write_text(t.replace(a,b,1),encoding="utf-8")
def replace_all(path,a,b):
 p=Path(path);t=p.read_text(encoding="utf-8")
 assert a in t,(path,a)
 p.write_text(t.replace(a,b),encoding="utf-8")

review=read("research/papauto-japan-next30-519-owner-review-2026-11-21.json")
assert review["status"]=="OWNER_APPROVED_RELEASE_519" and review["owner_approval"]["approved"] is True
assert review["review_pdf"]["sha256"]=="718076fc478c085c2df5b2197c498618ea8dc8cc59bf90dea3efd773409f3a5b"
assert review["review_media_zip"]["sha256"]=="61c618dbb89ed51866a9ed9618c6f7bed769a0fb2e2b0d2de8a3072c13ee8292"
assert review["review_full_manifest"]["sha256"]=="c79856a191f906983a713a20467f93f45231b01ed8ff0c6c8642c4fd84cdbfc3"
assert review["previous_catalog_count"]==489 and review["target_after_owner_approval"]==519 and len(review["selection"])==30
assert {x:(review["archive_sources"][x]["artifact_id"],review["archive_sources"][x]["manifest_sha256"]) for x in SPEC}=={x:(int(z[0]),z[1]) for x,z in SPEC.items()}
source={}
for name,(aid,expected) in SPEC.items():
 folder=Path("/tmp/papauto-japan519-source")/aid
 raw=(folder/"manifest.json").read_bytes()
 assert sha(raw)==expected,("source manifest changed",name)
 source[name]=(folder,{x["index"]:x for x in json.loads(raw)})
old=[]
for path in [
 "research/owner-selected-japan-lots-2026-11-14.json",
 "research/owner-approved-50-archive-2026-11-19.json",
 "research/owner-approved-second-50-archive-2026-11-19.json",
 "research/owner-approved-japan-atp-30-archive-2026-11-20.json",
 "research/owner-approved-japan-atp-second-30-archive-2026-11-20.json",
 "research/owner-approved-japan-atp-third-30-archive-2026-11-20.json",
 "research/owner-approved-japan-atp-fourth-30-archive-2026-11-20.json",
 "research/owner-approved-japan-atp-fifth-30-archive-2026-11-20.json",
 "research/owner-approved-japan-atp-sixth-30-archive-2026-11-21.json",
 "research/owner-approved-japan-drom991-gap-17-archive-2026-11-21.json",
 "research/owner-approved-japan-next30-2026-11-21.json",
 "research/owner-approved-japan-followup30-2026-11-21.json"]:old+=read(path)["lots"]
assert len(old)==457
keys={key(r) for r in old}
urls={r.get("source_listing") for r in old}
prior_hashes={h for r in old for h in r.get("media_sha256",[])}
seen=set();seen_urls=set();hashes=[];cards=[]
for ordinal,sel in enumerate(review["selection"],1):
 assert ordinal==sel["ordinal"] and sel["src"] in SPEC
 folder,archive=source[sel["src"]]
 record=archive[sel["index"]]
 assert key(record) not in keys and key(record) not in seen,(ordinal,"duplicate auction lot")
 assert record["source"] not in urls and record["source"] not in seen_urls,(ordinal,"duplicate listing")
 assert 0<record["cc"]<=2000 and 0<record["hp"]<=160 and record["km"]>0 and float(record["grade"])>=3.5 and record["price_jpy"]>0
 assert len(record["files"])==len(record["raw_sha256"])==len(record["media_urls"])==3
 assert record["source"].startswith("https://atp-auto.ru/") and all(str(u).startswith("https://7.tru.ru/imgs/") for u in record["media_urls"])
 match=re.fullmatch(r"(.+?) (20\d\d) года",record["title"])
 assert match and int(match.group(2))==record["year"]
 make,model=match.group(1).split(" ",1)
 seen.add(key(record));seen_urls.add(record["source"])
 ident=f"japan-next30-519-20261121-{ordinal:02d}"
 local=[];rowhash=[]
 for i,typ in enumerate(("front","rear","sheet")):
  p=folder/record["files"][i];raw=p.read_bytes();h=sha(raw)
  assert raw.startswith(b"\xff\xd8\xff") and h not in prior_hashes and h not in hashes
  with Image.open(BytesIO(raw)) as im:
   assert im.format=="JPEG" and min(im.size)>=(700 if typ=="sheet" else 180)
   im.verify()
  dest=Path(f"assets/auction/approved/{ident}-{typ}.jpg")
  assert not dest.exists()
  dest.write_bytes(raw)
  local.append("/"+dest.as_posix());rowhash.append(h);hashes.append(h)
 trim=str(record.get("trim") or "не указана")
 if "<" in trim or any(ord(ch)>127 for ch in trim):trim="не указана"
 desc=(f"{make} {model}, {record['year']} года, кузов {record['body']}, комплектация: {trim}. "
       f"Двигатель {record['cc']} см³, мощность {record['hp']} л.с. по данным источника. "
       f"Пробег по статистике источника (округлённый): {record['km']} км, оценка {record['grade']}, "
       f"аукцион {record['auction']}, дата {record['date']}, лот №{record['lot']}. "
       "Автомобиль не в наличии: историческая статистика аукционных продаж Японии. "
       "Цена аукциона не включает доставку, таможенные платежи и оформление.")
 cards.append(dict(id=ident,country="japan",make=make,model=model,year=record["year"],mileage_km=record["km"],
   body=record["body"],grade=record["grade"],auction=record["auction"],lot=str(record["lot"]),
   auction_date=record["date"],description=desc,photo_context="original_auction_lot",
   sheet_type="original_auction_sheet",photos=local[:2],auction_sheet=local[2],
   sale_status="reference_only",reported_price=record["price_jpy"],media_sha256=rowhash,
   source_listing=record["source"],source_media=record["media_urls"],raw_sha256=record["raw_sha256"],
   trim=trim,engine_cc=record["cc"],power_hp=record["hp"],rights_confirmed=False,
   artifact_record_index=sel["index"],artifact_id=int(SPEC[sel["src"]][0])))
assert len(cards)==30 and len(set(hashes))==90 and len(hashes)==90
assert sha("".join(hashes).encode())=="78d1cfa459e5f0eb0385ffcecaaff4ba8e694f0034a790730258d89015d141b9","Different image sequence from reviewed original ZIP"
path="research/owner-approved-japan-next30-519-2026-11-21.json"
receipt=dict(approved_count=30,approval_date="2026-11-21",rights_confirmed=False,
 owner_authorized_archival_reference_only=True,reviewed_pdf_sha256=review["review_pdf"]["sha256"],
 reviewed_jpg_zip_sha256=review["review_media_zip"]["sha256"],
 reviewed_full_manifest_sha256=review["review_full_manifest"]["sha256"],
 jpg_aggregate_sha256=sha("".join(hashes).encode()),lots=cards,
 note="Exactly 30 owner-approved source-linked archival photo/full-sheet records; no commercial image rights asserted.")
Path(path).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
blob=Path(path).read_bytes()
blobsha=hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()

replace_all("scripts/compile_auction_gallery.py","MAX_LOTS = 500","MAX_LOTS = 700")
sub("scripts/generate_auction_lot_pages.py","35 <= len(lots) <= 500","35 <= len(lots) <= 700")
insertion='''        # Owner-approved Japanese batch 489 -> 519, exact 30 reviewed in PDF.
        archive12 = json.loads((ROOT / "research/owner-approved-japan-next30-519-2026-11-21.json").read_text(encoding="utf-8"))
        archived12 = archive12["lots"]
        if (archive12.get("approved_count") != 30 or archive12.get("rights_confirmed") is not False
                or archive12.get("owner_authorized_archival_reference_only") is not True
                or archive12.get("reviewed_pdf_sha256") != "718076fc478c085c2df5b2197c498618ea8dc8cc59bf90dea3efd773409f3a5b"
                or archive12.get("reviewed_jpg_zip_sha256") != "61c618dbb89ed51866a9ed9618c6f7bed769a0fb2e2b0d2de8a3072c13ee8292"
                or [r["id"] for r in archived12] != [f"japan-next30-519-20261121-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived12)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: 519 reviewed PDF/media mismatch")
        hashes12 = [h for r in archived12 for h in r["media_sha256"]]
        if (len(hashes12) != 90 or len(set(hashes12 + hashes11 + hashes10 + hashes9 + hashes8 + hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 1355
                or hashlib.sha256("".join(hashes12).encode()).hexdigest() != "78d1cfa459e5f0eb0385ffcecaaff4ba8e694f0034a790730258d89015d141b9"):
            raise RuntimeError("PAPAUTO_POLICY: 519 photo / sheet media not exact reviewed originals")
        for rec in archived12:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
'''
sub("scripts/compile_auction_gallery.py",'    seen_lot_keys = {',insertion+'    seen_lot_keys = {')
sub("scripts/verify_publication_approval.py","FROZEN_SOURCE_BLOBS = {",
  'FROZEN_SOURCE_BLOBS = {\n    "'+path+'": "'+blobsha+'",')
sub("scripts/verify_publication_approval.py",
 '    approved_archive = {r["id"] for r in archive["lots"] + archive2["lots"] + archive3["lots"] + archive4["lots"] + archive5["lots"] + archive6["lots"] + archive7["lots"] + archive8["lots"] + archive9["lots"] + archive10["lots"] + archive11["lots"]}',
 '    archive12 = json.loads((ROOT / "'+path+'").read_text(encoding="utf-8"))\n'
 +'    approved_archive = {r["id"] for r in archive["lots"] + archive2["lots"] + archive3["lots"] + archive4["lots"] + archive5["lots"] + archive6["lots"] + archive7["lots"] + archive8["lots"] + archive9["lots"] + archive10["lots"] + archive11["lots"] + archive12["lots"]}')
sub("scripts/verify_publication_approval.py",'len(rows) != 489 or len(approved_archive) != 357','len(rows) != 519 or len(approved_archive) != 387')
sub("scripts/build_static_public.py",'gallery_result["count"] != 489 or gallery_result["new"] != 454','gallery_result["count"] != 519 or gallery_result["new"] != 484')
sub("scripts/build_static_public.py",'published_lot_count != 489','published_lot_count != 519')
replace_all("scripts/publish_lot_search.py","489","519")
sub("tests/test_site_warm_theme.py",'self.assertEqual(lots["lot_count"],489)','self.assertEqual(lots["lot_count"],519)')
sub("tests/test_auction_only_images_policy.py",'self.assertEqual(pub["lot_count"], 489)','self.assertEqual(pub["lot_count"], 519)')
for name in ("AGENTS.md","docs/AUCTION_ONLY_GALLERY.md"):
 p=Path(name);p.write_text(p.read_text(encoding="utf-8").rstrip()+"\n\nOn 2026-11-21, the owner explicitly approved the exact PapAuto_Japan_Another30_519_2026-11-21.pdf collection for an archival-only 30-card Japanese publication. Source-frozen receipt: "+path+". No street photos, no third-party commercial rights assertion, no dealer/competitor links or live inventory claims.\n",encoding="utf-8")
print("PAPAUTO_519_RELEASE_PREPARED: 30 source-backed verified lots, 90 original images, 489->519, frozen owner PDF")
