"""Publish the exact owner-reviewed ATP reference selection, not a general import exception."""
from pathlib import Path
import json,hashlib,re
from PIL import Image
R=Path('.')
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(Path(p).read_text())
f=read('research/japan-atp-fifth-30-review-2026-11-20.json')
assert f['reviewed_jpg_zip_sha256']=='05b2637633b0233d6cc8c9356fb799be8a507717f9a4db97cad38ac6e99b43e6'
spec=[(14635366908,44751477987,'5b4f81241a1a8e4f109272db4a3945a9b325f830093beb6de1e19049064d9b52',[1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,20,23,24]),(14636730038,44751845290,'9e9d04f781c4a0ef4991ba1581c93f7cd5e9eb418771cdd072367f2653c4cfa4',[1,2,3,4,5,6,7,8,9])]
rows=[]
for ref,(aid,rid,digest,ids) in zip(f['archives'],spec):
 assert (ref['artifact_id'],ref['source_run_id'],ref['manifest_sha256'],ref['selected_indices'])==(aid,rid,digest,ids)
 D=Path('/tmp/atp-verified')/str(aid)
 assert sha((D/'manifest.json').read_bytes())==digest
 available={x['index']:x for x in read(D/'manifest.json')}
 rows.extend(dict(available[i],artifact_id=aid,source_run_id=rid) for i in ids)
assert len(rows)==30
assert sha(''.join(h for x in rows for h in x['raw_sha256']).encode())=='b548aa8938230596cdfa4888885bc295284cec036688a1f68d52594cb16068c5'
old=[]
for p in ['research/owner-selected-japan-lots-2026-11-14.json','research/owner-approved-50-archive-2026-11-19.json','research/owner-approved-second-50-archive-2026-11-19.json','data/gallery-lots.json','research/owner-approved-japan-atp-30-archive-2026-11-20.json','research/owner-approved-japan-atp-second-30-archive-2026-11-20.json','research/owner-approved-japan-atp-third-30-archive-2026-11-20.json','research/owner-approved-japan-atp-fourth-30-archive-2026-11-20.json']:
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
 ident=f'japan-atp-b5-20261120-{i:02d}'
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
assert len(allhash)==90 and sha(''.join(allhash).encode())=='2fa31077037843840bd658e0d4da3ff11f4e06aca2f15b114ca375c237d72346'
for p,b in pending:p.write_bytes(b)
path='research/owner-approved-japan-atp-fifth-30-archive-2026-11-20.json'
manifest=dict(approval_date='2026-11-20',approved_count=30,owner_authorized_archival_reference_only=True,rights_confirmed=False,reviewed_jpg_zip_sha256=f['reviewed_jpg_zip_sha256'],reviewed_metadata_manifest_sha256=f['reviewed_metadata_manifest_sha256'],archives=f['archives'],raw_media_aggregate_sha256=f['raw_media_aggregate_sha256'],archive_media_aggregate_sha256=sha(''.join(allhash).encode()),owner_instruction='Утверждаю все 30 карточек PapAuto_Japan_30_ATP_batch5. Опубликуй их на PapAuto с оригинальными фотографиями и аукционными листами.',rights_note='Exact owner-approved archived examples only. Owner decision is not third-party license. Do not change ordinary import safeguards.',lots=records)
Path(path).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
def replace(p,a,b):
 q=Path(p);s=q.read_text();assert s.count(a)==1,(p,a,s.count(a));q.write_text(s.replace(a,b,1))
patch='''        # Exact ATP thirty-card owner-reviewed reference release.
        archive7 = json.loads((ROOT / "research/owner-approved-japan-atp-fifth-30-archive-2026-11-20.json").read_text(encoding="utf-8"))
        archived7 = archive7["lots"]
        if (archive7.get("approved_count") != 30 or archive7.get("rights_confirmed") is not False
                or archive7.get("owner_authorized_archival_reference_only") is not True
                or archive7.get("reviewed_jpg_zip_sha256") != "05b2637633b0233d6cc8c9356fb799be8a507717f9a4db97cad38ac6e99b43e6"
                or [r["id"] for r in archived7] != [f"japan-atp-b5-20261120-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived7)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: ATP archive review mismatch")
        hashes7 = [h for r in archived7 for h in r["media_sha256"]]
        if len(hashes7) != 90 or len(set(hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 944 or hashlib.sha256("".join(hashes7).encode()).hexdigest() != "2fa31077037843840bd658e0d4da3ff11f4e06aca2f15b114ca375c237d72346":
            raise RuntimeError("PAPAUTO_POLICY: ATP reviewed media mismatch")
        for rec in archived7:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
'''
replace('scripts/compile_auction_gallery.py','            additional.append(card)\n    seen_lot_keys','            additional.append(card)\n'+patch+'    seen_lot_keys')
replace('scripts/build_static_public.py','gallery_result["count"] != 352 or gallery_result["new"] != 317','gallery_result["count"] != 382 or gallery_result["new"] != 347')
replace('scripts/build_static_public.py','if published_lot_count != 352 or not lot_sitemap.is_file():','if published_lot_count != 382 or not lot_sitemap.is_file():')
b=Path(path).read_bytes();blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
replace('scripts/verify_publication_approval.py','FROZEN_SOURCE_BLOBS = {','FROZEN_SOURCE_BLOBS = {\n    "'+path+'": "'+blob+'",')
replace('scripts/verify_publication_approval.py','    approved_archive = {r["id"] for r in archive["lots"] + archive2["lots"] + archive3["lots"] + archive4["lots"] + archive5["lots"] + archive6["lots"]}','    archive7 = json.loads((ROOT / "'+path+'").read_text(encoding="utf-8"))\n    approved_archive = {r["id"] for r in archive["lots"] + archive2["lots"] + archive3["lots"] + archive4["lots"] + archive5["lots"] + archive6["lots"] + archive7["lots"]}')
replace('scripts/verify_publication_approval.py','len(rows) != 352 or len(approved_archive) != 220','len(rows) != 382 or len(approved_archive) != 250')
for a in ['352 аукционных лота из Японии','352 опубликованных примера','Все 352 аукционных лота']:
 replace('scripts/publish_lot_search.py',a,a.replace('352','382'))
replace('tests/test_auction_only_images_policy.py','self.assertEqual(pub["lot_count"], 352)','self.assertEqual(pub["lot_count"], 382)\n            atp5=json.loads((ROOT / "'+path+'").read_text(encoding="utf-8"))["lots"]\n            atp5_ids={r["id"] for r in atp5}\n            self.assertEqual(len(atp5_ids),30)\n            self.assertEqual(sum(lot["id"] in atp5_ids and lot["rights_confirmed"] is False and lot["status"]=="reference_only" and len(lot["photos"])==2 for lot in pub["lots"]),30)')
replace('tests/test_site_warm_theme.py','self.assertEqual(lots["lot_count"],352)','self.assertEqual(lots["lot_count"],382)')
for p in ['AGENTS.md','docs/AUCTION_ONLY_GALLERY.md']:
 q=Path(p);q.write_text(q.read_text().rstrip()+'\n\nOwner instruction 2026-11-20: exactly the 30 ATP archival examples from PapAuto_Japan_30_ATP_batch5_cards.zip authorized after review, receipt '+path+'. Only exact ninety frozen media digests; no third-party license assertion, no current stock claims, ordinary auction protections unchanged.\n')
print('382 total gallery records; ninety exact reviewed JPEGs verified; original archive source hashes retained.')
