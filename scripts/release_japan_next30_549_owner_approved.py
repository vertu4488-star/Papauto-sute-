"""Release exact 30 owner-approved Japanese archive records 519 -> 549 from staged immutable originals.

This code must run only after preceding 519 gallery is published, and with the
owner-approved stage receipt/JPEGs restored from the 549 staging review branch.
Source records are archival examples, rights_confirmed remains False.
"""
from pathlib import Path
import json, hashlib, re, shutil
from PIL import Image

ROOT=Path(".")
def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(b):return hashlib.sha256(b).hexdigest()
def norm(s):return re.sub("[^a-z0-9]","",str(s).lower())
def key(r):return (norm(r["auction"]),str(r.get("auction_date") or r.get("date") or "")[:10],str(r.get("lot") or r.get("lot_number") or "").lstrip("0"))
def sub(path,a,b):
 p=Path(path);s=p.read_text(encoding="utf-8");assert s.count(a)==1,(path,a[:65],s.count(a))
 p.write_text(s.replace(a,b,1),encoding="utf-8")

staged=read("research/owner-approved-japan-next30-549-staged-2026-11-21.json")
assert staged["status"]=="OWNER_APPROVED_STAGED_PENDING_519_RELEASE"
assert staged["owner_approved_count"]==30 and staged["media_count"]==90 and staged["published"] is False
assert staged["source_review_pdf_sha256"]=="7f1209ab57d0fa02acea28fdb33bb82d91f3c1a7027dcefb563da057265aa024"
assert staged["source_review_zip_sha256"]=="405bb0643dc4baf67f67ff92f0e51a67e62d5b77b1e391005dbccf8e9ac33242"
assert staged["source_full_review_json_sha256"]=="ce57eae5efc12860b259ad93bc3de15c137a91e6f2367340fb23da16e1f2f18e"
assert staged["staged_media_aggregate_sha256"]=="14335eb0d5d9ec636a49ee0d9001f595bebf32ef18b060ebcce69a45e9e3589f"
preceding=read("research/owner-approved-japan-next30-519-2026-11-21.json")
assert preceding["approved_count"]==30 and preceding["reviewed_pdf_sha256"]=="718076fc478c085c2df5b2197c498618ea8dc8cc59bf90dea3efd773409f3a5b"
assert len(preceding["lots"])==30
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
 "research/owner-approved-japan-followup30-2026-11-21.json",
]:old+=read(path)["lots"]
old+=preceding["lots"]
assert len(old)==487
oldkeys={key(r) for r in old};old_urls={r.get("source_listing") for r in old}
oldhash={h for r in old for h in r.get("media_sha256",[])}
new=[];hashes=[];seen_keys=set();seen_urls=set()
for n,row in enumerate(staged["lots"],1):
 assert row["ordinal"]==n and row["id"]==f"japan-next30-549-20261121-{n:02d}"
 assert row["rights_confirmed"] is False and row["published"] is False
 assert 0<row["power_hp"]<=160 and 0<row["engine_cc"]<=2000 and row["mileage_km"]>0 and float(row["grade"])>=3.5
 assert row["reported_price"]>0 and len(row["staged_photos"])==2 and row["staged_auction_sheet"]
 assert key(row) not in oldkeys and key(row) not in seen_keys,("duplicate lot",n)
 assert row["source_listing"] not in old_urls and row["source_listing"] not in seen_urls,("duplicate listing",n)
 seen_keys.add(key(row));seen_urls.add(row["source_listing"])
 assets=[];rowhash=[]
 for idx,(kind,rel) in enumerate(zip(("front","rear","sheet"),row["staged_photos"]+[row["staged_auction_sheet"]])):
  source=Path(rel)
  assert source.as_posix().startswith("research/japan-549-staged-media/")
  raw=source.read_bytes();digest=sha(raw)
  assert digest==row["staged_media_sha256"][idx] and digest not in oldhash and digest not in hashes
  assert raw.startswith(b"\xff\xd8\xff")
  with Image.open(source) as im:
   assert im.format=="JPEG" and min(im.size)>=(700 if kind=="sheet" else 180)
   im.verify()
  dest=Path(f"assets/auction/approved/japan-next30-549-20261121-{n:02d}-{kind}.jpg")
  assert not dest.exists()
  dest.write_bytes(raw)
  assets.append("/"+dest.as_posix());rowhash.append(digest);hashes.append(digest)
 trim=str(row.get("trim") or "не указана")
 if "<" in trim or any(ord(ch)>127 for ch in trim):trim="не указана"
 desc=(f"{row['make']} {row['model']}, {row['year']} года, кузов {row['body']}, комплектация: {trim}. "
       f"Двигатель {row['engine_cc']} см³, мощность {row['power_hp']} л.с. по данным источника. "
       f"Пробег по статистике источника (округлённый): {row['mileage_km']} км, оценка {row['grade']}, "
       f"аукцион {row['auction']}, дата {row['auction_date']}, лот №{row['lot']}. "
       "Автомобиль не в наличии: историческая статистика аукционных продаж Японии. "
       "Цена аукциона не включает доставку, таможенные платежи и оформление.")
 new.append(dict(id=row["id"],country="japan",make=row["make"],model=row["model"],year=row["year"],
 mileage_km=row["mileage_km"],body=row["body"],grade=row["grade"],auction=row["auction"],
 lot=row["lot"],auction_date=row["auction_date"],description=desc,photo_context="original_auction_lot",
 sheet_type="original_auction_sheet",photos=assets[:2],auction_sheet=assets[2],
 sale_status="reference_only",reported_price=row["reported_price"],media_sha256=rowhash,
 source_listing=row["source_listing"],source_media=row["source_media"],trim=trim,
 engine_cc=row["engine_cc"],power_hp=row["power_hp"],rights_confirmed=False,
 artifact_record_index=row["artifact_record_index"],artifact_id=row["artifact_id"],
 raw_sha256=row["raw_source_sha256"]))
assert len(new)==30 and len(hashes)==90 and len(set(hashes))==90
assert sha("".join(hashes).encode())=="14335eb0d5d9ec636a49ee0d9001f595bebf32ef18b060ebcce69a45e9e3589f"
receipt_path="research/owner-approved-japan-next30-549-2026-11-21.json"
receipt=dict(approved_count=30,approval_date="2026-11-21",rights_confirmed=False,
 owner_authorized_archival_reference_only=True,reviewed_pdf_sha256=staged["source_review_pdf_sha256"],
 reviewed_jpg_zip_sha256=staged["source_review_zip_sha256"],
 reviewed_full_manifest_sha256=staged["source_full_review_json_sha256"],
 jpg_aggregate_sha256=sha("".join(hashes).encode()),lots=new,
 note="Approved release of exact 30 Japan historical references after 519; third-party commercial rights not asserted.")
Path(receipt_path).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
blob=Path(receipt_path).read_bytes()
gitblob=hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()
insert='''        # Exact 30 user-approved Japan examples after separate 519 release.
        archive13 = json.loads((ROOT / "research/owner-approved-japan-next30-549-2026-11-21.json").read_text(encoding="utf-8"))
        archived13 = archive13["lots"]
        if (archive13.get("approved_count") != 30 or archive13.get("rights_confirmed") is not False
                or archive13.get("owner_authorized_archival_reference_only") is not True
                or archive13.get("reviewed_pdf_sha256") != "7f1209ab57d0fa02acea28fdb33bb82d91f3c1a7027dcefb563da057265aa024"
                or archive13.get("reviewed_jpg_zip_sha256") != "405bb0643dc4baf67f67ff92f0e51a67e62d5b77b1e391005dbccf8e9ac33242"
                or [r["id"] for r in archived13] != [f"japan-next30-549-20261121-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived13)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: 549 PDF/ZIP or media mis-match")
        hashes13 = [h for r in archived13 for h in r["media_sha256"]]
        if (len(hashes13) != 90 or len(set(hashes13 + hashes12 + hashes11 + hashes10 + hashes9 + hashes8 + hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 1445
                or hashlib.sha256("".join(hashes13).encode()).hexdigest() != "14335eb0d5d9ec636a49ee0d9001f595bebf32ef18b060ebcce69a45e9e3589f"):
            raise RuntimeError("PAPAUTO_POLICY: duplicate or tampered 549 original source photo / sheet")
        for rec in archived13:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
'''
sub("scripts/compile_auction_gallery.py","    seen_lot_keys = {",insert+"    seen_lot_keys = {")
sub("scripts/verify_publication_approval.py","FROZEN_SOURCE_BLOBS = {",'FROZEN_SOURCE_BLOBS = {\n    "'+receipt_path+'": "'+gitblob+'",')
sub("scripts/verify_publication_approval.py",
 '    approved_archive = {r["id"] for r in archive["lots"] + archive2["lots"] + archive3["lots"] + archive4["lots"] + archive5["lots"] + archive6["lots"] + archive7["lots"] + archive8["lots"] + archive9["lots"] + archive10["lots"] + archive11["lots"] + archive12["lots"]}',
 '    archive13 = json.loads((ROOT / "'+receipt_path+'").read_text(encoding="utf-8"))\n'
 +'    approved_archive = {r["id"] for r in archive["lots"] + archive2["lots"] + archive3["lots"] + archive4["lots"] + archive5["lots"] + archive6["lots"] + archive7["lots"] + archive8["lots"] + archive9["lots"] + archive10["lots"] + archive11["lots"] + archive12["lots"] + archive13["lots"]}')
sub("scripts/verify_publication_approval.py","len(rows) != 519 or len(approved_archive) != 387","len(rows) != 549 or len(approved_archive) != 417")
sub("scripts/build_static_public.py",'gallery_result["count"] != 519 or gallery_result["new"] != 484','gallery_result["count"] != 549 or gallery_result["new"] != 514')
sub("scripts/build_static_public.py","published_lot_count != 519","published_lot_count != 549")
p=Path("scripts/publish_lot_search.py");t=p.read_text(encoding="utf-8");assert "519" in t;p.write_text(t.replace("519","549"),encoding="utf-8")
sub("tests/test_site_warm_theme.py",'self.assertEqual(lots["lot_count"],519)','self.assertEqual(lots["lot_count"],549)')
sub("tests/test_auction_only_images_policy.py",'self.assertEqual(pub["lot_count"], 519)','self.assertEqual(pub["lot_count"], 549)')
for name in ("AGENTS.md","docs/AUCTION_ONLY_GALLERY.md"):
 p=Path(name);p.write_text(p.read_text(encoding="utf-8").rstrip()+"\n\nOn 2026-11-21, user expressly approved 30 original photo/full-sheet Japan archive records in PapAuto_Japan_Another30_549_2026-11-21.pdf to be published after the previously approved 519 release. Receipt: "+receipt_path+". No unrelated or missing photos, no stock/real-time sales claims, rights_confirmed=false. All auction-only restrictions remain.\n",encoding="utf-8")
print("PAPAUTO_549_RELEASE_PREPARED: 30 additional exact-source lots, 90 real images, site 519->549")
