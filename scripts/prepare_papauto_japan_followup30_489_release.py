"""Release 30 exact owner-directed additional Japanese auction lots, taking PapAuto from 459 to 489."""
from pathlib import Path
import json,hashlib,re
from PIL import Image
ROOT=Path(".")
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def norm(s):return re.sub("[^a-z0-9]","",str(s).lower())
def key(r):return norm(r["auction"]),str(r.get("auction_date") or r.get("date") or "")[:10],str(r.get("lot") or r.get("lot_number") or "").lstrip("0")
def replace(path,a,b):
 p=Path(path);s=p.read_text(encoding="utf-8");assert s.count(a)==1,(path,a[:65],s.count(a));p.write_text(s.replace(a,b,1),encoding="utf-8")
f=read("research/papauto-japan-followup30-direct-release-2026-11-21.json")
assert f["status"]=="OWNER_DIRECTED_RELEASE" and f["approved_additional_lots"]==30 and f["prior_live_japan_lots"]==459 and f["target_japan_lots"]==489
assert f["review_pdf_sha256"]=="01c7362b9575b09db0157b0e66189d8b518fc3037481b25d924d34ca72a9c29a"
assert f["review_zip_sha256"]=="218466b04049b91abe543e23c00572ac1f63f6cc6b3c5b3ac8ab441179f35a7e"
assert f["raw_sha256_aggregate"]=="62c19e7a046f49d0f32f969724202bf0133e206a8a133513cad5741e8b919d6c"
assert f["jpg_sha256_aggregate"]=="be9ffa7575b7e8cf707c952e95098f8b51880d59c169a28418ed91172660dc64"
specs={
 "wave3":(14691820564,44864961085,"9bd14bac931dbacfb3fc2578cf52816ce9fd5a2b6c666d04eff9ec42c01ebdc2"),
 "b6":(14641252098,44758942918,"fe2fb3d5f95195e9fd084dc72a5ad4f349dd9f100195bf1e5c5d13bfb1c58838")
}
assert {x["key"]: (x["artifact_id"],x["run_id"],x["manifest_sha256"]) for x in f["source_archives"]}==specs
sources={}
for name,(aid,run,digest) in specs.items():
 D=Path("/tmp/papauto-next30-original")/str(aid)
 assert D.is_dir() and sha((D/"manifest.json").read_bytes())==digest,("source artifact mismatch",name)
 sources[name]=(D,{x["index"]:x for x in read(D/"manifest.json")})
assert len(f["selection"])==30
old=[]
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
 "research/owner-approved-japan-drom991-gap-17-archive-2026-11-21.json",
 "research/owner-approved-japan-next30-2026-11-21.json",
]:old+=read(p)["lots"]
oldkeys=set(map(key,old));oldsrc={x.get("source_listing") for x in old}
prior={sha(p.read_bytes()) for p in Path("assets/auction/approved").iterdir() if p.is_file()}
cards=[];out=[];hashes=[];keys=set();seen_src=set();selected_indices={k:[] for k in specs}
for i,sel in enumerate(f["selection"],1):
 assert sel["ordinal"]==i and sel["src"] in specs
 D,manifest=sources[sel["src"]]
 x=manifest[sel["index"]]
 assert x["title"].casefold()==(sel["name"]+" года").casefold(),(i,"source-title mismatch")
 assert 2000<=x["year"]<=2026 and x["date"] and x["auction"] and x["lot"]
 assert len(x["raw_sha256"])==len(x["media_urls"])==len(x["files"])==3
 assert x["source"].startswith("https://atp-auto.ru/") and all(a.startswith("https://7.tru.ru/imgs/") for a in x["media_urls"])
 assert 0<x["hp"]<=160 and 0<x["cc"]<=2000 and x["km"]>0 and x["price_jpy"]>0 and float(x["grade"])>=3.5
 k=key(x);assert k not in keys and k not in oldkeys and x["source"] not in seen_src and x["source"] not in oldsrc,("duplicate",i,k)
 keys.add(k);seen_src.add(x["source"]);selected_indices[sel["src"]].append(sel["index"])
 ident=f"japan-followup30-20261121-{i:02d}"
 make,model=re.sub(r" 20\d\d года$","",x["title"]).split(" ",1);model=model.title()
 paths=[];record_hashes=[]
 for j,kind in enumerate(("front","rear","sheet")):
  src=D/x["files"][j];b=src.read_bytes();h=sha(b)
  assert b.startswith(b"\xff\xd8\xff") and h not in prior and h not in hashes,("duplicate media",i,kind)
  with Image.open(src) as im:
   assert min(im.size)>=(700 if j==2 else 180),(i,kind,im.size)
   im.verify()
  dest=Path(f"assets/auction/approved/{ident}-{kind}.jpg")
  assert not dest.exists()
  hashes.append(h);record_hashes.append(h);paths.append("/"+str(dest));out.append((dest,b))
 trim=str(x.get("trim") or "не уточнена").strip()
 if any(ord(ch)>127 for ch in trim) or "<" in trim:trim="не уточнена"
 desc=(f"{make} {model}, {x['year']} года, кузов {x['body']}, комплектация по источнику: {trim}. "
       f"Двигатель {x['cc']} см³, {x['hp']} л.с. по данным источника (для гибрида не суммарная мощность системы). "
       f"Пробег по статистике источника (округлённый) {x['km']} км, оценка {x['grade']}, "
       f"аукцион {x['auction']}, дата {x['date']}, лот №{x['lot']}. "
       "История аукционных продаж Японии. Автомобиль не в наличии и не предложение о продаже. "
       "Цена аукциона без доставки, пошлин и оформления.")
 aid,run,_=specs[sel["src"]]
 cards.append(dict(id=ident,country="japan",make=make,model=model,year=x["year"],mileage_km=x["km"],
  source_rounded_mileage_km=x["km"],body=x["body"],grade=x["grade"],auction=x["auction"],
  lot=x["lot"],auction_date=x["date"],description=desc,photo_context="original_auction_lot",
  sheet_type="original_auction_sheet",photos=paths[:2],auction_sheet=paths[2],sale_status="reference_only",
  reported_price=x["price_jpy"],media_sha256=record_hashes,raw_sha256=x["raw_sha256"],
  source_listing=x["source"],source_media=x["media_urls"],trim=trim,
  engine_cc=x["cc"],power_hp=x["hp"],rights_confirmed=False,reviewed_card_number=i,
  artifact_record_index=x["index"],artifact_id=aid,source_run_id=run))
assert len(cards)==30 and len(hashes)==len(out)==90 and len(set(hashes))==90
assert sha("".join(hashes).encode())=="be9ffa7575b7e8cf707c952e95098f8b51880d59c169a28418ed91172660dc64"
assert {k:sorted(v) for k,v in selected_indices.items()}=={k:sorted(next(x["selected_indices"] for x in f["source_archives"] if x["key"]==k)) for k in specs}
for path,b in out:path.write_bytes(b)
receipt_path="research/owner-approved-japan-followup30-2026-11-21.json"
receipt=dict(approval_date="2026-11-21",approved_count=30,owner_authorized_archival_reference_only=True,
 rights_confirmed=False,reviewed_pdf_sha256=f["review_pdf_sha256"],
 reviewed_jpg_zip_sha256=f["review_zip_sha256"],
 reviewed_manifest_sha256=f["raw_sha256_aggregate"],
 archive_media_aggregate_sha256=f["jpg_sha256_aggregate"],archives=f["source_archives"],
 owner_instruction="Owner requested another thirty exact Japanese auction cards after prior published 459, with genuine photographs and complete sheets.",
 rights_note="Historic reference only, third-party rights not independently verified.",lots=cards)
Path(receipt_path).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
patch='''        # Owner-directed thirty additional exact-source Japan auction reference examples.
        archive11 = json.loads((ROOT / "research/owner-approved-japan-followup30-2026-11-21.json").read_text(encoding="utf-8"))
        archived11 = archive11["lots"]
        if (archive11.get("approved_count") != 30 or archive11.get("rights_confirmed") is not False
                or archive11.get("owner_authorized_archival_reference_only") is not True
                or archive11.get("reviewed_pdf_sha256") != "01c7362b9575b09db0157b0e66189d8b518fc3037481b25d924d34ca72a9c29a"
                or archive11.get("reviewed_jpg_zip_sha256") != "218466b04049b91abe543e23c00572ac1f63f6cc6b3c5b3ac8ab441179f35a7e"
                or [r["id"] for r in archived11] != [f"japan-followup30-20261121-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived11)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: exact owner-directed next30 photo+sheet digest mismatch")
        hashes11 = [h for r in archived11 for h in r["media_sha256"]]
        if (len(hashes11) != 90
                or len(set(hashes11 + hashes10 + hashes9 + hashes8 + hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 1265
                or hashlib.sha256("".join(hashes11).encode()).hexdigest() != "be9ffa7575b7e8cf707c952e95098f8b51880d59c169a28418ed91172660dc64"):
            raise RuntimeError("PAPAUTO_POLICY: thirty additional original JPEGs/damage sheets duplicate or tampered")
        for rec in archived11:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
'''
replace("scripts/compile_auction_gallery.py",
 "            additional.append(card)\n    seen_lot_keys",
 "            additional.append(card)\n"+patch+"    seen_lot_keys")
replace("scripts/build_static_public.py",'gallery_result["count"] != 459 or gallery_result["new"] != 424','gallery_result["count"] != 489 or gallery_result["new"] != 454')
replace("scripts/build_static_public.py",'if published_lot_count != 459 or not lot_sitemap.is_file():','if published_lot_count != 489 or not lot_sitemap.is_file():')
blob=Path(receipt_path).read_bytes()
gitblob=hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()
replace("scripts/verify_publication_approval.py","FROZEN_SOURCE_BLOBS = {",
 'FROZEN_SOURCE_BLOBS = {\n    "'+receipt_path+'": "'+gitblob+'",')
replace("scripts/verify_publication_approval.py",
 '    approved_archive = {r["id"] for r in archive["lots"] + archive2["lots"] + archive3["lots"] + archive4["lots"] + archive5["lots"] + archive6["lots"] + archive7["lots"] + archive8["lots"] + archive9["lots"] + archive10["lots"]}',
 '    archive11 = json.loads((ROOT / "'+receipt_path+'").read_text(encoding="utf-8"))\n'
 +'    approved_archive = {r["id"] for r in archive["lots"] + archive2["lots"] + archive3["lots"] + archive4["lots"] + archive5["lots"] + archive6["lots"] + archive7["lots"] + archive8["lots"] + archive9["lots"] + archive10["lots"] + archive11["lots"]}')
replace("scripts/verify_publication_approval.py",'len(rows) != 459 or len(approved_archive) != 327','len(rows) != 489 or len(approved_archive) != 357')
for a in ("459 аукционных лота из Японии","459 опубликованных примера","Все 459 аукционных лота"):
 replace("scripts/publish_lot_search.py",a,a.replace("459","489"))
replace("tests/test_auction_only_images_policy.py",'            self.assertEqual(pub["lot_count"], 459)',
 '            self.assertEqual(pub["lot_count"], 489)\n'
 +'            next30=json.loads((ROOT / "'+receipt_path+'").read_text(encoding="utf-8"))["lots"]\n'
 +'            next30_ids={r["id"] for r in next30}\n'
 +'            self.assertEqual(len(next30_ids),30)\n'
 +'            self.assertEqual(sum(lot["id"] in next30_ids and lot["rights_confirmed"] is False and lot["status"]=="reference_only" and len(lot["photos"])==2 for lot in pub["lots"]),30)')
replace("tests/test_site_warm_theme.py",'self.assertEqual(lots["lot_count"],459)','self.assertEqual(lots["lot_count"],489)')
for path in ("AGENTS.md","docs/AUCTION_ONLY_GALLERY.md"):
 q=Path(path);q.write_text(q.read_text().rstrip()+"\n\nOwner directed on 2026-11-21 another 30 archival Japan auction photo+sheet records. Source-reviewed PDF PapAuto_Japan_Another30_489_2026-11-21.pdf, receipt "+receipt_path+". Ninety immutable JPEGs, all matching complete auction sheets. Statistics only, no inventory or third-party license assertion. All normal image-only release restrictions preserved.\n")
print("PAPAUTO_489_RELEASE_PREPARED: 30 verified new lots, 90 images, 459 -> 489")
