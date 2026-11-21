"""Publish the exact owner-reviewed ATP reference selection, not a general import exception."""
from pathlib import Path
import json,hashlib,re
from PIL import Image
R=Path('.')
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(Path(p).read_text())
f=read('research/japan-atp-sixth-30-review-2026-11-20.json')
assert f['reviewed_jpg_zip_sha256']=='298d7269884a28dbc14505d46149615dc5bf9cbb4b30f3f18ab40d08b807e121'
spec=[(14641252098,44758942918,'fe2fb3d5f95195e9fd084dc72a5ad4f349dd9f100195bf1e5c5d13bfb1c58838',[5,6,14,15,18,19,21,31,39,42,44,45,48,49,56,73,79,86,93,99,116,130,134,138,148,151,171,185,187,193])]
rows=[]
for ref,(aid,rid,digest,ids) in zip(f['archives'],spec):
 assert (ref['artifact_id'],ref['source_run_id'],ref['manifest_sha256'],ref['selected_indices'])==(aid,rid,digest,ids)
 D=Path('/tmp/atp-verified')/str(aid)
 assert sha((D/'manifest.json').read_bytes())==digest
 available={x['index']:x for x in read(D/'manifest.json')}
 rows.extend(dict(available[i],artifact_id=aid,source_run_id=rid) for i in ids)
assert len(rows)==30
assert sha(''.join(h for x in rows for h in x['raw_sha256']).encode())=='df5ebac79a0de9ecb764fcef94f28e1a628d73cd47031b8904d54c71583363aa'
old=[]
for p in ['research/owner-selected-japan-lots-2026-11-14.json','research/owner-approved-50-archive-2026-11-19.json','research/owner-approved-second-50-archive-2026-11-19.json','data/gallery-lots.json','research/owner-approved-japan-atp-30-archive-2026-11-20.json','research/owner-approved-japan-atp-second-30-archive-2026-11-20.json','research/owner-approved-japan-atp-third-30-archive-2026-11-20.json','research/owner-approved-japan-atp-fourth-30-archive-2026-11-20.json','research/owner-approved-japan-atp-fifth-30-archive-2026-11-20.json']:
 old+=read(p)['lots']
def key(x):return re.sub(r'[^a-z0-9]','',x['auction'].lower()),str(x.get('auction_date',x.get('date','')))[:10],str(x.get('lot',x.get('lot_number',''))).lstrip('0')
assert len(set(map(key,rows)))==30 and not set(map(key,rows))&set(map(key,old))
assert not {x['source'] for x in rows}&{x.get('source_listing') for x in old}
assets=R/'assets/auction/approved'
prior={sha(p.read_bytes()) for p in assets.iterdir() if p.is_file()}
assert len(f['sheet_mileage_km'])==len(f['reviewed_trim'])==30
allhash=[];records=[];pending=[]
for i,x in enumerate(rows,1):
 assert x['source'].startswith('https://atp-auto.ru/') and len(x['files'])==len(x['raw_sha256'])==len(x['media_urls'])==3
 assert all(u.startswith('https://7.tru.ru/imgs/') for u in x['media_urls'])
 assert 0<x['hp']<=160 and 0<x['cc']<=2000 and x['km']>0 and x['price_jpy']>0 and float(x['grade'])>=3.5
 ident=f'japan-atp-b6-20261121-{i:02d}'
 make,model=re.sub(r' 20\d\d года$','',x['title']).split(' ',1)
 local=[];hashes=[]
 for n,kind in enumerate(['front','rear','sheet']):
  src=Path('/tmp/atp-verified')/str(x['artifact_id'])/x['files'][n];b=src.read_bytes();h=sha(b)
  assert b.startswith(b'\xff\xd8\xff') and h not in prior and h not in allhash
  with Image.open(src) as im:
   assert min(im.size)>=180
   im.verify()
  allhash.append(h);hashes.append(h);p=f'assets/auction/approved/{ident}-{kind}.jpg'
  assert not Path(p).exists();local.append('/'+p);pending.append((Path(p),b))
 mileage=f['sheet_mileage_km'][i-1];trim=f['reviewed_trim'][i-1]
 assert abs(mileage-x['km'])<=1000,(i,mileage,x['km'])
 power=None if model.lower()=='roomy' and 'G-T' in trim else x['hp']
 power_text=f'{power} л.с. по данным источника (для гибрида не суммарная мощность системы)' if power is not None else 'мощность требует уточнения'
 desc=f"{make} {model} {x['year']} года, кузов {x['body']}, комплектация {trim}, двигатель {x['cc']} см³, {power_text}. Пробег по аукционному листу {mileage} км, оценка {x['grade']}, аукцион {x['auction']}, дата {x['date']}, лот №{x['lot']}. Статистика продаж на аукционах Японии. Автомобиль не в наличии и не предложение о продаже. Цена по данным аукциона, без доставки и оформления."
 records.append(dict(id=ident,country='japan',make=make,model=model,year=x['year'],mileage_km=mileage,source_rounded_mileage_km=x['km'],body=x['body'],grade=x['grade'],auction=x['auction'],lot=x['lot'],auction_date=x['date'],description=desc,photo_context='original_auction_lot',sheet_type='original_auction_sheet',photos=local[:2],auction_sheet=local[2],sale_status='reference_only',reported_price=x['price_jpy'],media_sha256=hashes,raw_sha256=x['raw_sha256'],source_listing=x['source'],source_media=x['media_urls'],trim=trim,engine_cc=x['cc'],power_hp=power,source_reported_power_hp=x['hp'],rights_confirmed=False,reviewed_card_number=i,artifact_record_index=x['index'],artifact_id=x['artifact_id'],source_run_id=x['source_run_id']))
assert len(allhash)==90 and sha(''.join(allhash).encode())=='5e057a358b0e1adc74975716eaa42b0940ce322aaf2932d5f0d49c004ef62355'
for p,b in pending:p.write_bytes(b)
path='research/owner-approved-japan-atp-sixth-30-archive-2026-11-21.json'
manifest=dict(approval_date='2026-11-21',approved_count=30,owner_authorized_archival_reference_only=True,rights_confirmed=False,reviewed_jpg_zip_sha256=f['reviewed_jpg_zip_sha256'],reviewed_metadata_manifest_sha256=f['reviewed_metadata_manifest_sha256'],archives=f['archives'],raw_media_aggregate_sha256=f['raw_media_aggregate_sha256'],archive_media_aggregate_sha256=sha(''.join(allhash).encode()),owner_instruction='Утверждаю все 30 карточек PapAuto_Japan_30_ATP_batch6. Опубликуй их на PapAuto с оригинальными фотографиями и аукционными листами.',rights_note='Exact owner-approved archived examples only. Owner decision is not third-party license. Do not change ordinary import safeguards.',lots=records)
Path(path).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
def replace(p,a,b):
 q=Path(p);s=q.read_text();assert s.count(a)==1,(p,a,s.count(a));q.write_text(s.replace(a,b,1))
patch='''        # Exact ATP thirty-card owner-reviewed reference release.
        archive8 = json.loads((ROOT / "research/owner-approved-japan-atp-sixth-30-archive-2026-11-21.json").read_text(encoding="utf-8"))
        archived8 = archive8["lots"]
        if (archive8.get("approved_count") != 30 or archive8.get("rights_confirmed") is not False
                or archive8.get("owner_authorized_archival_reference_only") is not True
                or archive8.get("reviewed_jpg_zip_sha256") != "298d7269884a28dbc14505d46149615dc5bf9cbb4b30f3f18ab40d08b807e121"
                or [r["id"] for r in archived8] != [f"japan-atp-b6-20261121-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived8)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: ATP archive review mismatch")
        hashes8 = [h for r in archived8 for h in r["media_sha256"]]
        if len(hashes8) != 90 or len(set(hashes8 + hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 1034 or hashlib.sha256("".join(hashes8).encode()).hexdigest() != "5e057a358b0e1adc74975716eaa42b0940ce322aaf2932d5f0d49c004ef62355":
            raise RuntimeError("PAPAUTO_POLICY: ATP reviewed media mismatch")
        for rec in archived8:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
'''
replace('scripts/compile_auction_gallery.py','            additional.append(card)\n    seen_lot_keys','            additional.append(card)\n'+patch+'    seen_lot_keys')
replace('scripts/build_static_public.py','gallery_result["count"] != 382 or gallery_result["new"] != 347','gallery_result["count"] != 412 or gallery_result["new"] != 377')
replace('scripts/build_static_public.py','if published_lot_count != 382 or not lot_sitemap.is_file():','if published_lot_count != 412 or not lot_sitemap.is_file():')
b=Path(path).read_bytes();blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
replace('scripts/verify_publication_approval.py','FROZEN_SOURCE_BLOBS = {','FROZEN_SOURCE_BLOBS = {\n    "'+path+'": "'+blob+'",')
replace('scripts/verify_publication_approval.py','    approved_archive = {r["id"] for r in archive["lots"] + archive2["lots"] + archive3["lots"] + archive4["lots"] + archive5["lots"] + archive6["lots"] + archive7["lots"]}','    archive8 = json.loads((ROOT / "'+path+'").read_text(encoding="utf-8"))\n    approved_archive = {r["id"] for r in archive["lots"] + archive2["lots"] + archive3["lots"] + archive4["lots"] + archive5["lots"] + archive6["lots"] + archive7["lots"] + archive8["lots"]}')
replace('scripts/verify_publication_approval.py','len(rows) != 382 or len(approved_archive) != 250','len(rows) != 412 or len(approved_archive) != 280')
for a in ['382 аукционных лота из Японии','382 опубликованных примера','Все 382 аукционных лота']:
 replace('scripts/publish_lot_search.py',a,a.replace('382','412'))
replace('tests/test_auction_only_images_policy.py','self.assertEqual(pub["lot_count"], 382)','self.assertEqual(pub["lot_count"], 412)\n            atp6=json.loads((ROOT / "'+path+'").read_text(encoding="utf-8"))["lots"]\n            atp6_ids={r["id"] for r in atp6}\n            self.assertEqual(len(atp6_ids),30)\n            self.assertEqual(sum(lot["id"] in atp6_ids and lot["rights_confirmed"] is False and lot["status"]=="reference_only" and len(lot["photos"])==2 for lot in pub["lots"]),30)')
replace('tests/test_site_warm_theme.py','self.assertEqual(lots["lot_count"],382)','self.assertEqual(lots["lot_count"],412)')
for p in ['AGENTS.md','docs/AUCTION_ONLY_GALLERY.md']:
 q=Path(p);q.write_text(q.read_text().rstrip()+'\n\nOwner instruction 2026-11-21: exactly the 30 ATP archival examples from PapAuto_Japan_30_auction_cards_review_2026-11-21.pdf authorized after review, receipt '+path+'. Only exact ninety frozen media digests; no third-party license assertion, no current stock claims, ordinary auction protections unchanged.\n')
print('382 total gallery records; ninety exact reviewed JPEGs verified; original archive source hashes retained.')
