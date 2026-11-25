"""Exact 7 owner-reviewed archival examples, no claim of media license or live stock."""
from pathlib import Path
from io import BytesIO
import hashlib,json,re
from collections import Counter
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path("/tmp/honda7")
RECEIPT="research/owner-approved-japan-honda7-2026-11-25.json"
MANIFEST="a76e03a4eb27438465e7fc8217cd665f877c24987994accf0677c48fa2938b16"
PDF="11b3680fd8e1ac78c97a4c5d6aa0ec26044890c6896ce9d4eed3c603dae6b01a"
ZIP="57ceab5200b48491df0a9785e91fa374e832ba6cc2380995c65154d8195f92b8"
SEQ="47cdeed143dbe5398ff3e4eb2fb54ec5429641b8e30660fbd25bee43d4fb6ff8"
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def norm(v):return re.sub(r"[^a-z0-9]","",str(v).lower())
def key(r):return norm(r["auction"]),str(r.get("date") or r.get("auction_date"))[:10],str(r.get("lot") or r.get("lot_number")).lstrip("0")
def patch(path,old,new):
 p=ROOT/path;s=p.read_text(encoding="utf-8");assert s.count(old)==1,(path,old,s.count(old));p.write_text(s.replace(old,new,1),encoding="utf-8")
raw=(SOURCE/"manifest.json").read_bytes()
assert sha(raw)==MANIFEST
rows=json.loads(raw);assert len(rows)==9 and [r["index"] for r in rows]==list(range(1,10))
SELECTED=[1,3,4,5,6,8,9]
rows=[r for r in rows if r["index"] in SELECTED]
assert [r["index"] for r in rows]==SELECTED
prior=[]
for p in [ROOT/"data/gallery-lots.json",ROOT/"data/approved-auction-lots.json",ROOT/"research/owner-selected-japan-lots-2026-11-14.json",*sorted((ROOT/"research").glob("owner-approved-*archive*.json")),*sorted((ROOT/"research").glob("owner-approved-japan-*.json"))]:
 j=read(p)
 prior.extend(x for x in j.get("lots",[]) if x.get("auction") and (x.get("lot") or x.get("lot_number")))
keys={key(x) for x in prior};urls={x.get("source_listing") for x in prior}
hashes={h for x in prior for h in x.get("media_sha256",[])+x.get("raw_sha256",[])}
# Check prior actual media bytes, including historical baseline assets.
for p in (ROOT/"assets/auction").rglob("*"):
 if p.is_file() and p.suffix.lower() in {".jpg",".jpeg",".png",".webp"}:hashes.add(sha(p.read_bytes()))
used=[];lots=[];counts=Counter();pending=[]
for r in rows:
 m=re.fullmatch(r"(.+?) (20\d\d) года",r["title"]);assert m and int(m[2])==r["year"]
 make,model=m[1].split(" ",1);counts[make+" "+model.lower()]+=1
 assert key(r) not in keys and r["source"] not in urls
 keys.add(key(r));urls.add(r["source"])
 assert r["source"].startswith("https://atp-auto.ru/") and len(r["media_urls"])==3 and all(x.startswith("https://7.tru.ru/imgs/") for x in r["media_urls"])
 assert len(r["files"])==3 and len(r["raw_sha256"])==3
 assert 0<r["cc"]<=1900 and r["hp"] is None and r["km"]>0 and r["price_jpy"]>0 and float(r["grade"])>=3.5
 ident=f'japan-honda7-20261125-{r["index"]:02d}'
 media=[];digests=[]
 for i,role in enumerate(("front","rear","sheet")):
  f=r["files"][i];assert f==f'{r["index"]:03d}-{i}.jpg'
  data=(SOURCE/f).read_bytes();digest=sha(data)
  assert digest not in hashes and digest not in used and len(data)>3000
  with Image.open(BytesIO(data)) as im:
   assert im.format=="JPEG" and min(im.size)>=(700 if role=="sheet" else 180);im.verify()
  dest=ROOT/f"assets/auction/approved/{ident}-{role}.jpg";assert not dest.exists()
  pending.append((dest,data));media.append("/"+dest.relative_to(ROOT).as_posix());digests.append(digest);used.append(digest)
 trim=str(r.get("trim") or "не указана")
 desc=(f"{make} {model}, {r['year']} года, кузов {r['body']}, комплектация: {trim}. "
       f"Двигатель {r['cc']} см³; мощность в источнике не указана, уточняется по документам. "
       f"Пробег по статистике источника (округлённый): {r['km']} км, оценка {r['grade']}. "
       f"Аукцион {r['auction']}, дата {r['date']}, лот №{r['lot']}. "
       "Автомобиль не в наличии: исторический пример из японской аукционной статистики. "
       "Цена по источнику не включает доставку, таможенные платежи и оформление.")
 lots.append(dict(id=ident,country="japan",make=make,model=model,year=r["year"],mileage_km=r["km"],body=r["body"],grade=r["grade"],auction=r["auction"],lot=str(r["lot"]),auction_date=r["date"],description=desc,photo_context="original_auction_lot",sheet_type="original_auction_sheet",photos=media[:2],auction_sheet=media[2],sale_status="reference_only",reported_price=r["price_jpy"],media_sha256=digests,source_listing=r["source"],source_media=r["media_urls"],raw_sha256=r["raw_sha256"],trim=trim,engine_cc=r["cc"],power_hp=r["hp"],rights_confirmed=False,artifact_record_index=r["index"],artifact_id=14997444386))
assert counts==Counter({"Honda n van":3,"Honda n one":3,"Honda wr-v":1}),counts
assert len(used)==21 and sha("".join(used).encode())==SEQ
for p,b in pending:p.write_bytes(b)
receipt=dict(approved_count=7,approval_date="2026-11-25",rights_confirmed=False,owner_authorized_archival_reference_only=True,reviewed_pdf_sha256=PDF,reviewed_jpg_zip_sha256=ZIP,reviewed_full_manifest_sha256=MANIFEST,jpg_aggregate_sha256=SEQ,lots=lots,note="Owner explicitly approved and requested publication of exactly 7 PDF-reviewed archive examples; independent commercial media rights not confirmed. No stock or verified sale claim.")
p=ROOT/RECEIPT;assert not p.exists();p.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
b=p.read_bytes();blob=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
append=f'''        archive19 = json.loads((ROOT / "{RECEIPT}").read_text(encoding="utf-8"))
        archived19 = archive19["lots"]
        if (archive19.get("approved_count") != 7 or archive19.get("rights_confirmed") is not False
                or archive19.get("owner_authorized_archival_reference_only") is not True
                or archive19.get("reviewed_pdf_sha256") != "{PDF}"
                or archive19.get("reviewed_jpg_zip_sha256") != "{ZIP}"
                or archive19.get("reviewed_full_manifest_sha256") != "{MANIFEST}"
                or [r["id"] for r in archived19] != [f"japan-honda7-20261125-{{i:02d}}" for i in (1,3,4,5,6,8,9)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived19)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: exact 7 Honda archive receipt mismatch")
        hashes19 = [h for r in archived19 for h in r["media_sha256"]]
        prior19 = prior18 + hashes18
        if (len(hashes19) != 21 or len(set(hashes19)) != 21 or set(hashes19).intersection(prior19)
                or hashlib.sha256("".join(hashes19).encode()).hexdigest() != "{SEQ}"):
            raise RuntimeError("PAPAUTO_POLICY: 7 Honda image/sheet originals altered or reused")
        for rec in archived19:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Цена по данным аукциона", rights_confirmed=False)
            additional.append(card)
'''
patch("scripts/compile_auction_gallery.py","    seen_lot_keys = {",append+"    seen_lot_keys = {")
patch("scripts/verify_publication_approval.py","FROZEN_SOURCE_BLOBS = {",f'FROZEN_SOURCE_BLOBS = {{\n    "{RECEIPT}": "{blob}",')
patch("scripts/verify_publication_approval.py",'    approved_archive = {r["id"] for r in archive18["lots"]',f'    archive19 = json.loads((ROOT / "{RECEIPT}").read_text(encoding="utf-8"))\n    approved_archive = {{r["id"] for r in archive19["lots"] + archive18["lots"]')
patch("scripts/verify_publication_approval.py","len(rows) != 659 or len(approved_archive) != 527","len(rows) != 666 or len(approved_archive) != 534")
patch("scripts/build_static_public.py",'gallery_result["count"] != 659 or gallery_result["new"] != 624','gallery_result["count"] != 666 or gallery_result["new"] != 631')
patch("scripts/build_static_public.py","published_lot_count != 659","published_lot_count != 666")
patch("tests/test_site_warm_theme.py",'self.assertEqual(lots["lot_count"],659)','self.assertEqual(lots["lot_count"],666)')
patch("tests/test_auction_only_images_policy.py",'self.assertEqual(pub["lot_count"], 659)','self.assertEqual(pub["lot_count"], 666)')
for f in ("AGENTS.md","docs/AUCTION_ONLY_GALLERY.md"):
 p=ROOT/f;p.write_text(p.read_text(encoding="utf-8").rstrip()+"\n\nOwner approved the exact PDF PapAuto_Honda_7_ATP_review_2026-11-25.pdf and explicitly requested publication. Exact 7 archived source examples / 21 frozen JPEGs only; "+RECEIPT+". No commercial license assertion, no live inventory, no general exception for other records.\n",encoding="utf-8")
print("PAPAUTO_7_HONDA_ARCHIVE_PREPARED",len(lots),len(used))
