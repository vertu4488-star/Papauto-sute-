"""Exact 18 owner-reviewed archival examples, no claim of media license or live stock."""
from pathlib import Path
from io import BytesIO
import hashlib,json,re
from collections import Counter
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path("/tmp/japan18")
RECEIPT="research/owner-approved-japan-gap18-2026-11-25.json"
MANIFEST="eb9ddd1cd10667393075f289e530d02633a8f101f8f2c0afff2390a11e36bfd9"
PDF="3b8b5ed6adb46bf5ac23d52c8a3e08f760f9352df6809d5fc3ee8cc00dbb8154"
ZIP="4984e9ac975f41a7087e5a0bee25b2a137dd7030a4844ffc9532c55c8d6f4533"
SEQ="38400fb152f953d1f1a771ec56cef4a931e420a099c8955716161cdbf1d129ca"
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def norm(v):return re.sub(r"[^a-z0-9]","",str(v).lower())
def key(r):return norm(r["auction"]),str(r.get("date") or r.get("auction_date"))[:10],str(r.get("lot") or r.get("lot_number")).lstrip("0")
def patch(path,old,new):
 p=ROOT/path;s=p.read_text(encoding="utf-8");assert s.count(old)==1,(path,old,s.count(old));p.write_text(s.replace(old,new,1),encoding="utf-8")
raw=(SOURCE/"manifest.json").read_bytes()
assert sha(raw)==MANIFEST
rows=json.loads(raw);assert len(rows)==18 and [r["index"] for r in rows]==list(range(1,19))
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
 assert 0<r["cc"]<=2000 and 0<r["hp"]<=160 and r["km"]>0 and r["price_jpy"]>0 and float(r["grade"])>=3.5
 ident=f'japan-gap18-20261125-{r["index"]:02d}'
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
       f"Двигатель {r['cc']} см³, мощность {r['hp']} л.с. по данным источника. "
       f"Пробег по статистике источника (округлённый): {r['km']} км, оценка {r['grade']}. "
       f"Аукцион {r['auction']}, дата {r['date']}, лот №{r['lot']}. "
       "Автомобиль не в наличии: исторический пример из японской аукционной статистики. "
       "Цена по источнику не включает доставку, таможенные платежи и оформление.")
 lots.append(dict(id=ident,country="japan",make=make,model=model,year=r["year"],mileage_km=r["km"],body=r["body"],grade=r["grade"],auction=r["auction"],lot=str(r["lot"]),auction_date=r["date"],description=desc,photo_context="original_auction_lot",sheet_type="original_auction_sheet",photos=media[:2],auction_sheet=media[2],sale_status="reference_only",reported_price=r["price_jpy"],media_sha256=digests,source_listing=r["source"],source_media=r["media_urls"],raw_sha256=r["raw_sha256"],trim=trim,engine_cc=r["cc"],power_hp=r["hp"],rights_confirmed=False,artifact_record_index=r["index"],artifact_id=14997159442))
assert counts==Counter({"Toyota bb":3,"Toyota pixis epoch":3,"Toyota pixis joy":3,"Toyota pixis mega":3,"Nissan juke":3,"Nissan moco":3}),counts
assert len(used)==54 and sha("".join(used).encode())==SEQ
for p,b in pending:p.write_bytes(b)
receipt=dict(approved_count=18,approval_date="2026-11-25",rights_confirmed=False,owner_authorized_archival_reference_only=True,reviewed_pdf_sha256=PDF,reviewed_jpg_zip_sha256=ZIP,reviewed_full_manifest_sha256=MANIFEST,jpg_aggregate_sha256=SEQ,lots=lots,note="Owner explicitly approved and requested publication of exactly 18 PDF-reviewed archive examples; independent commercial media rights not confirmed. No stock or verified sale claim.")
p=ROOT/RECEIPT;assert not p.exists();p.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
b=p.read_bytes();blob=hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
append=f'''        archive18 = json.loads((ROOT / "{RECEIPT}").read_text(encoding="utf-8"))
        archived18 = archive18["lots"]
        if (archive18.get("approved_count") != 18 or archive18.get("rights_confirmed") is not False
                or archive18.get("owner_authorized_archival_reference_only") is not True
                or archive18.get("reviewed_pdf_sha256") != "{PDF}"
                or archive18.get("reviewed_jpg_zip_sha256") != "{ZIP}"
                or archive18.get("reviewed_full_manifest_sha256") != "{MANIFEST}"
                or [r["id"] for r in archived18] != [f"japan-gap18-20261125-{{i:02d}}" for i in range(1,19)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived18)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: exact 18 archive receipt mismatch")
        hashes18 = [h for r in archived18 for h in r["media_sha256"]]
        prior18 = hashes16 + hashes15 + hashes14 + hashes13 + hashes12 + hashes11 + hashes10 + hashes9 + hashes8 + hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes + [h for r in archive17["lots"] for h in r["media_sha256"]]
        if (len(hashes18) != 54 or len(set(hashes18)) != 54 or set(hashes18).intersection(prior18)
                or hashlib.sha256("".join(hashes18).encode()).hexdigest() != "{SEQ}"):
            raise RuntimeError("PAPAUTO_POLICY: 18 image/sheet originals altered or reused")
        for rec in archived18:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Цена по данным аукциона", rights_confirmed=False)
            additional.append(card)
'''
patch("scripts/compile_auction_gallery.py","    seen_lot_keys = {",append+"    seen_lot_keys = {")
patch("scripts/verify_publication_approval.py","FROZEN_SOURCE_BLOBS = {",f'FROZEN_SOURCE_BLOBS = {{\n    "{RECEIPT}": "{blob}",')
patch("scripts/verify_publication_approval.py",'    approved_archive = {r["id"] for r in archive["lots"]',f'    archive18 = json.loads((ROOT / "{RECEIPT}").read_text(encoding="utf-8"))\n    approved_archive = {{r["id"] for r in archive18["lots"] + archive["lots"]')
patch("scripts/verify_publication_approval.py","len(rows) != 641 or len(approved_archive) != 509","len(rows) != 659 or len(approved_archive) != 527")
patch("scripts/build_static_public.py",'gallery_result["count"] != 641 or gallery_result["new"] != 606','gallery_result["count"] != 659 or gallery_result["new"] != 624')
patch("scripts/build_static_public.py","published_lot_count != 641","published_lot_count != 659")
patch("tests/test_site_warm_theme.py",'self.assertEqual(lots["lot_count"],641)','self.assertEqual(lots["lot_count"],659)')
patch("tests/test_auction_only_images_policy.py",'self.assertEqual(pub["lot_count"], 641)','self.assertEqual(pub["lot_count"], 659)')
for f in ("AGENTS.md","docs/AUCTION_ONLY_GALLERY.md"):
 p=ROOT/f;p.write_text(p.read_text(encoding="utf-8").rstrip()+"\n\nOwner approved the exact PDF PapAuto_Japan_18_ATP_review_2026-11-25.pdf and explicitly requested publication. Exact 18 archived source examples / 54 frozen JPEGs only; "+RECEIPT+". No commercial license assertion, no live inventory, no general exception for other records.\n",encoding="utf-8")
print("PAPAUTO_18_EXACT_ARCHIVE_PREPARED",len(lots),len(used))
