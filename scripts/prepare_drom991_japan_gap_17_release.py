"""Append precisely the seventeen owner-directed archival Japan lots matching Drom model/year gaps.
Checks exact source artifact and photo/sheet hashes; preserves all ordinary import gates.
"""
from pathlib import Path
import json, hashlib, re
from PIL import Image

ROOT=Path(".")
P=Path("research/drom991-japan-gap-17-review-2026-11-21.json")
f=json.loads(P.read_text())
def sha(data): return hashlib.sha256(data).hexdigest()
def data(path): return json.loads(Path(path).read_text())
SELECTED=[1,2,4,5,8,10,11,12,13,14,15,16,17,18,19,21,22]
assert f["selected_indices"]==SELECTED and f["counts"]["new_lots"]==17 and f["counts"]["target_gallery"]==429
assert f["source_artifact"]["artifact_id"]==14689434591
assert f["source_artifact"]["source_run_id"]==44860801866
assert f["source_artifact"]["archive_sha256"]=="cff3e9449482429946d741008dd5056dc8117d6bf241688d1f928dc6cfe74de8"
D=Path("/tmp/drom-verified/14689434591")
assert sha((D/"manifest.json").read_bytes())=="6f7c1b2d9fdc9231b330f5880038cadd70583be681f0f45b4b032a222d9b5005"
allsource={x["index"]:x for x in data(D/"manifest.json")}
rows=[allsource[i] for i in SELECTED]
assert len(rows)==17 and sha("".join(h for x in rows for h in x["raw_sha256"]).encode())=="4d9d75a7a8cf88a24ef1f8de2ddd7e4cd012f09d75116c3b80efe2df94505a93"
existing=[]
for p in [
 "research/owner-selected-japan-lots-2026-11-14.json",
 "research/owner-approved-50-archive-2026-11-19.json",
 "research/owner-approved-second-50-archive-2026-11-19.json",
 "data/gallery-lots.json",
 "research/owner-approved-japan-atp-30-archive-2026-11-20.json",
 "research/owner-approved-japan-atp-second-30-archive-2026-11-20.json",
 "research/owner-approved-japan-atp-third-30-archive-2026-11-20.json",
 "research/owner-approved-japan-atp-fourth-30-archive-2026-11-20.json",
 "research/owner-approved-japan-atp-fifth-30-archive-2026-11-20.json",
 "research/owner-approved-japan-atp-sixth-30-archive-2026-11-21.json",
]:
 existing.extend(data(p)["lots"])
def lotkey(x):
 return (re.sub("[^a-z0-9]","",str(x["auction"]).lower()),
         str(x.get("auction_date",x.get("date","")))[:10],
         str(x.get("lot",x.get("lot_number",""))).lstrip("0"))
assert len(set(map(lotkey,rows)))==17 and not set(map(lotkey,rows))&set(map(lotkey,existing))
assert not {x["source"] for x in rows}&{x.get("source_listing") for x in existing}
prior={sha(p.read_bytes()) for p in Path("assets/auction/approved").iterdir() if p.is_file()}
newhash=[]; cards=[]; output=[]
for i,x in enumerate(rows,1):
 assert x["source"].startswith("https://atp-auto.ru/") and len(x["files"])==len(x["raw_sha256"])==len(x["media_urls"])==3
 assert all(u.startswith("https://7.tru.ru/imgs/") for u in x["media_urls"])
 assert 0<x["hp"]<=160 and 0<x["cc"]<=2000 and x["km"]>0 and x["price_jpy"]>0 and float(x["grade"])>=3.5
 identifier=f"japan-drom991-gap-20261121-{i:02d}"
 make,model=re.sub(r" 20\d\d года$","",x["title"]).split(" ",1)
 model=model.title()
 paths=[]; hashes=[]
 for n,kind in enumerate(("front","rear","sheet")):
  src=D/x["files"][n]; b=src.read_bytes(); h=sha(b)
  assert b.startswith(b"\xff\xd8\xff") and h not in prior and h not in newhash
  with Image.open(src) as im:
   assert min(im.size)>=180
   if n==2: assert min(im.size)>=500,("only damage diagram, not full sheet",i,im.size)
   im.verify()
  newhash.append(h);hashes.append(h)
  dest=Path(f"assets/auction/approved/{identifier}-{kind}.jpg")
  assert not dest.exists()
  paths.append("/"+str(dest));output.append((dest,b))
 trim=str(x.get("trim") or "не уточнена").strip()
 if any(ord(ch)>127 for ch in trim) or "<" in trim: trim="не уточнена"
 desc=(f"{make} {model}, {x['year']} года, кузов {x['body']}, комплектация по источнику: {trim}. "
       f"Двигатель {x['cc']} см³, мощность {x['hp']} л.с. по данным источника (для гибрида не суммарная мощность системы). "
       f"Пробег по статистике поставщика (округлённый) {x['km']} км, оценка {x['grade']}, "
       f"аукцион {x['auction']}, дата {x['date']}, лот №{x['lot']}. "
       "Статистика продаж аукционов Японии. Автомобиль не в наличии и не предложение о продаже. "
       "Цена по данным аукциона, без доставки и оформления.")
 cards.append(dict(
  id=identifier,country="japan",make=make,model=model,year=x["year"],mileage_km=x["km"],
  source_rounded_mileage_km=x["km"],body=x["body"],grade=x["grade"],auction=x["auction"],
  lot=x["lot"],auction_date=x["date"],description=desc,photo_context="original_auction_lot",
  sheet_type="original_auction_sheet",photos=paths[:2],auction_sheet=paths[2],
  sale_status="reference_only",reported_price=x["price_jpy"],media_sha256=hashes,
  raw_sha256=x["raw_sha256"],source_listing=x["source"],source_media=x["media_urls"],
  trim=trim,engine_cc=x["cc"],power_hp=x["hp"],rights_confirmed=False,
  reviewed_card_number=i,artifact_record_index=x["index"],
  artifact_id=14689434591,source_run_id=44860801866))
assert len(cards)==17 and len(newhash)==51
assert sha("".join(newhash).encode())=="7b3dcbded01e63464131da937f8b41c020ccf8aea56081bff3e413d012c8b75a"
for path,b in output: path.write_bytes(b)
receipt_path="research/owner-approved-japan-drom991-gap-17-archive-2026-11-21.json"
receipt=dict(approval_date="2026-11-21",approved_count=17,
 owner_authorized_archival_reference_only=True,rights_confirmed=False,
 reviewed_jpg_zip_sha256=f["source_artifact"]["archive_sha256"],
 reviewed_metadata_manifest_sha256=f["source_artifact"]["manifest_sha256"],
 archives=[dict(artifact_id=14689434591,source_run_id=44860801866,
                manifest_sha256=f["source_artifact"]["manifest_sha256"],selected_indices=SELECTED)],
 raw_media_aggregate_sha256=f["selected_source_raw_aggregate_sha256"],
 archive_media_aggregate_sha256=sha("".join(newhash).encode()),
 owner_instruction=f["publication_instruction"],
 rights_note="Owner authorized sourcing and addition. No third-party media license implied; archived examples only; source mileage rounded.",
 lots=cards)
Path(receipt_path).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
def replace(path,old,new):
 q=Path(path); s=q.read_text()
 assert s.count(old)==1,(path,old[:80],s.count(old))
 q.write_text(s.replace(old,new,1))
patch='''        # Exactly seventeen user-directed genuine Drom-priority Japanese auction archive examples.
        archive9 = json.loads((ROOT / "research/owner-approved-japan-drom991-gap-17-archive-2026-11-21.json").read_text(encoding="utf-8"))
        archived9 = archive9["lots"]
        if (archive9.get("approved_count") != 17 or archive9.get("rights_confirmed") is not False
                or archive9.get("owner_authorized_archival_reference_only") is not True
                or archive9.get("reviewed_jpg_zip_sha256") != "cff3e9449482429946d741008dd5056dc8117d6bf241688d1f928dc6cfe74de8"
                or [r["id"] for r in archived9] != [f"japan-drom991-gap-20261121-{i:02d}" for i in range(1,18)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived9)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: exact Drom-priority source photo-sheet archive mismatch")
        hashes9 = [h for r in archived9 for h in r["media_sha256"]]
        if len(hashes9) != 51 or len(set(hashes9 + hashes8 + hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 1085 or hashlib.sha256("".join(hashes9).encode()).hexdigest() != "7b3dcbded01e63464131da937f8b41c020ccf8aea56081bff3e413d012c8b75a":
            raise RuntimeError("PAPAUTO_POLICY: Drom-priority gallery media mismatch")
        for rec in archived9:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
'''
replace("scripts/compile_auction_gallery.py",
        "            additional.append(card)\n    seen_lot_keys",
        "            additional.append(card)\n"+patch+"    seen_lot_keys")
replace("scripts/build_static_public.py",
        'gallery_result["count"] != 412 or gallery_result["new"] != 377',
        'gallery_result["count"] != 429 or gallery_result["new"] != 394')
replace("scripts/build_static_public.py",
        'if published_lot_count != 412 or not lot_sitemap.is_file():',
        'if published_lot_count != 429 or not lot_sitemap.is_file():')
blob=Path(receipt_path).read_bytes()
gitblob=hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()
replace("scripts/verify_publication_approval.py",
        "FROZEN_SOURCE_BLOBS = {",
        'FROZEN_SOURCE_BLOBS = {\n    "'+receipt_path+'": "'+gitblob+'",')
replace("scripts/verify_publication_approval.py",
        '    approved_archive = {r["id"] for r in archive["lots"] + archive2["lots"] + archive3["lots"] + archive4["lots"] + archive5["lots"] + archive6["lots"] + archive7["lots"] + archive8["lots"]}',
        '    archive9 = json.loads((ROOT / "'+receipt_path+'").read_text(encoding="utf-8"))\n'
        '    approved_archive = {r["id"] for r in archive["lots"] + archive2["lots"] + archive3["lots"] + archive4["lots"] + archive5["lots"] + archive6["lots"] + archive7["lots"] + archive8["lots"] + archive9["lots"]}')
replace("scripts/verify_publication_approval.py",
        'len(rows) != 412 or len(approved_archive) != 280',
        'len(rows) != 429 or len(approved_archive) != 297')
for a in ("412 аукционных лота из Японии","412 опубликованных примера","Все 412 аукционных лота"):
 replace("scripts/publish_lot_search.py",a,a.replace("412","429"))
replace("tests/test_auction_only_images_policy.py",
        'self.assertEqual(pub["lot_count"], 412)',
        'self.assertEqual(pub["lot_count"], 429)\n'
        '            dromgap=json.loads((ROOT / "'+receipt_path+'").read_text(encoding="utf-8"))["lots"]\n'
        '            approved_ids={r["id"] for r in dromgap}\n'
        '            self.assertEqual(len(approved_ids),17)\n'
        '            self.assertEqual(sum(lot["id"] in approved_ids and lot["rights_confirmed"] is False and lot["status"]=="reference_only" and len(lot["photos"])==2 for lot in pub["lots"]),17)')
replace("tests/test_site_warm_theme.py",
        'self.assertEqual(lots["lot_count"],412)',
        'self.assertEqual(lots["lot_count"],429)')
for path in ("AGENTS.md","docs/AUCTION_ONLY_GALLERY.md"):
 q=Path(path)
 q.write_text(q.read_text().rstrip()+"\n\nOwner instruction 2026-11-21: select and add missing model-year Japanese auction examples in the Drom 991 project. Exactly 17 source photo+full-sheet pairs reviewed; source file "+receipt_path+". Fifty-one immutable JPEGs; rounded source mileage, no current inventory, no commercial media license assertion. Ordinary auction-only release restrictions remain active.\n")
print("PAPAUTO_429_RELEASE_PREPARED: seventeen real gap cards, 51 exact JPEGs, sources frozen.")
