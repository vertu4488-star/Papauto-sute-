"""Release only the second exact owner-reviewed 50-card archival set."""
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import json,hashlib,io,re
import requests
from PIL import Image
import pillow_avif
R=Path.cwd()
D=R/'research/next-50-20261119'
receipt=json.loads((D/'owner-exact-approval.json').read_text())
assert receipt['approved_count']==50 and receipt['owner_authorized_archival_reference_only'] is True and receipt['rights_confirmed'] is False
assert receipt['reviewed_pdf_sha256']=='8f9f0e37d605e5f4faced72994f4c9e246c02d886b213a379dfcd3acd18ac9bc'
ids=receipt['source_uuids']
assert len(ids)==len(set(ids))==50
by_id={x['source'].strip('/').split('/')[-1]:x for p in sorted(D.glob('part-*.json')) for x in json.loads(p.read_text())}
rows=[by_id[i] for i in ids]
fields=['model','year','num','date','price','spec','urls','source','auction','source_status','conflicting_sale_status']
metadata=[{k:x[k] for k in fields} for x in rows]
meta_hash=hashlib.sha256(json.dumps(metadata,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
assert meta_hash=='d7d0c912b61dbde46ff8604e9fb549f7c4892adce7fd5d3fd94f9e130d4abc2f',meta_hash
def digest(b):return hashlib.sha256(b).hexdigest()
old=[]
for name in ['research/owner-selected-japan-lots-2026-11-14.json','research/owner-approved-50-archive-2026-11-19.json','data/gallery-lots.json']:
    old.extend(json.loads((R/name).read_text())['lots'])
def norm(s):return re.sub(r'[^a-z0-9]+','',str(s).lower())
def date(s):
    try:return datetime.strptime(s,'%d.%m.%Y').date().isoformat()
    except ValueError:return s[:10]
def key(x):return norm(x['auction']),date(x.get('auction_date',x.get('date',''))),str(x.get('lot',x.get('lot_number',x.get('num','')))).lstrip('0')
keys={key(x) for x in old}
assert len(set(map(key,rows)))==50 and not keys.intersection(map(key,rows))
assert not {x['source'] for x in rows}.intersection(x.get('source_listing') for x in old)
def load(pair):
    page,x=pair
    assert x['source_status']=='archive displays sold' and x['conflicting_sale_status'] is False
    ident=f'japan-archive-b2-20261119-{page:02d}'
    raw=[];media=[]
    for idx,kind in enumerate(['sheet','front','rear']):
        u=x['urls'][idx]
        assert u.startswith('https://japan.storage.yandexcloud.net/') and ids[page-1] in u
        z=requests.get(u,timeout=28);z.raise_for_status();raw.append(digest(z.content))
        im=Image.open(io.BytesIO(z.content)).convert('RGB')
        assert min(im.size)>=180
        buf=io.BytesIO();im.save(buf,format='JPEG',quality=96,subsampling=0)
        media.append((f'{ident}-{kind}.jpg',buf.getvalue()))
    sp=x['spec'];make,model=x['model'].split(' ',1)
    km=int(re.sub(r'\D','',sp['Пробег:']))
    cc=int(re.search(r'\d+',sp['Объем:'])[0]);assert 0<cc<=2000
    amount=int(re.sub(r'\D','',x['price']));assert amount>0
    trim=sp.get('Комплектация:','').replace('\\*','*')
    grade=sp['Оценка:'];assert re.fullmatch(r'[3456](?:\.[05])?|[RSАA]',grade)
    assert sp['Кузов:'] and x['auction']
    desc=f"{x['model']} {x['year']} года, кузов {sp['Кузов:']}, комплектация {trim}, двигатель {cc} см³ ({sp.get('Двигатель:','—')}), КПП {sp.get('КПП:','—')}. Пробег {km} км, оценка {grade}, аукцион {x['auction']}, {x['date']}, лот №{x['num']}. Статистика продаж на аукционах Японии. Автомобиль не в наличии и не предложение о продаже. Цена по данным аукциона, без доставки и оформления."
    order=[1,2,0]
    result=dict(id=ident,country='japan',make=make,model=model,year=int(x['year']),mileage_km=km,body=sp['Кузов:'],grade=grade,auction=x['auction'],lot=x['num'],auction_date=date(x['date']),description=desc,photo_context='original_auction_lot',sheet_type='original_auction_sheet',photos=['/assets/auction/approved/'+media[k][0] for k in [1,2]],auction_sheet='/assets/auction/approved/'+media[0][0],sale_status='reference_only',reported_price=amount,media_sha256=[digest(media[k][1]) for k in order],source_listing=x['source'],source_media=[x['urls'][k] for k in order],trim=trim,engine_cc=cc,power_hp=int(re.search(r'\d+',sp['Мощность:'])[0]) if re.search(r'\d+',sp.get('Мощность:','')) else None,rights_confirmed=False,reviewed_pdf_page=page)
    return result,media,raw
with ThreadPoolExecutor(max_workers=8) as pool: built=list(pool.map(load,enumerate(rows,1)))
raw_hashes=[h for z in built for h in z[2]]
assert len(set(raw_hashes))==150 and digest(''.join(raw_hashes).encode())==receipt['raw_media_aggregate_sha256'],'Original source bytes differ from reviewed selection'
records=[z[0] for z in built]
new_hashes={h for z in records for h in z['media_sha256']}
assert len(new_hashes)==150
assets=R/'assets/auction/approved'
for p in assets.glob('*'):
    if p.is_file():assert digest(p.read_bytes()) not in new_hashes, f'Duplicate published photo: {p}'
# Persist only after the exact whole batch passes.
for _,media,_ in built:
    for name,data in media:(assets/name).write_bytes(data)
manifest_path='research/owner-approved-second-50-archive-2026-11-19.json'
manifest=dict(approval_date='2026-11-19',approved_count=50,owner_authorized_archival_reference_only=True,rights_confirmed=False,reviewed_pdf_sha256=receipt['reviewed_pdf_sha256'],raw_media_aggregate_sha256=receipt['raw_media_aggregate_sha256'],reviewed_metadata_sha256=meta_hash,owner_instruction=receipt['owner_instruction'],rights_note='Owner authorization is not third-party permission. Ordinary import rules unchanged.',lots=records)
(R/manifest_path).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
def replace(path,old,new):
    p=R/path;s=p.read_text();assert s.count(old)==1,(path,old,s.count(old));p.write_text(s.replace(old,new,1))
def blob_id(path):
    b=(R/path).read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
marker='            additional.append(card)\n'
patch='''        # Second exact 50-card owner-reviewed release, separate from prior batch.
        archive2 = json.loads((ROOT / "research/owner-approved-second-50-archive-2026-11-19.json").read_text(encoding="utf-8"))
        archived2 = archive2["lots"]
        if (archive2.get("approved_count") != 50 or archive2.get("rights_confirmed") is not False
                or archive2.get("owner_authorized_archival_reference_only") is not True
                or archive2.get("reviewed_pdf_sha256") != "8f9f0e37d605e5f4faced72994f4c9e246c02d886b213a379dfcd3acd18ac9bc"
                or archive2.get("raw_media_aggregate_sha256") != "53d5b85abd81282fb0e37e169617da7a08eb7562a5f77d35ab127e073432065b"
                or [r["id"] for r in archived2] != [f"japan-archive-b2-20261119-{i:02d}" for i in range(1,51)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived2)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: second archive review mismatch")
        hashes2 = [h for r in archived2 for h in r["media_sha256"]]
        if len(hashes2) != 150 or len(set(hashes2 + hashes + media_hashes)) != 494:
            raise RuntimeError("PAPAUTO_POLICY: duplicate second batch media")
        for rec in archived2:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
'''
replace('scripts/compile_auction_gallery.py',marker,marker+patch)
replace('scripts/build_static_public.py','gallery_result["count"] != 182 or gallery_result["new"] != 147','gallery_result["count"] != 232 or gallery_result["new"] != 197')
replace('scripts/build_static_public.py','if published_lot_count != 182 or not lot_sitemap.is_file():','if published_lot_count != 232 or not lot_sitemap.is_file():')
replace('scripts/verify_publication_approval.py','FROZEN_SOURCE_BLOBS = {','FROZEN_SOURCE_BLOBS = {\n    "'+manifest_path+'": "'+blob_id(manifest_path)+'",')
replace('scripts/verify_publication_approval.py','    approved_archive = {r["id"] for r in archive["lots"]}\n','    archive2 = json.loads((ROOT / "'+manifest_path+'").read_text(encoding="utf-8"))\n    approved_archive = {r["id"] for r in archive["lots"] + archive2["lots"]}\n')
replace('scripts/verify_publication_approval.py','len(rows) != 182 or len(approved_archive) != 50','len(rows) != 232 or len(approved_archive) != 100')
replace('scripts/publish_lot_search.py','182 аукционных лота из Японии','232 аукционных лота из Японии')
replace('scripts/publish_lot_search.py','182 опубликованных примера','232 опубликованных примера')
replace('scripts/publish_lot_search.py','Все 182 аукционных лота','Все 232 аукционных лота')
replace('tests/test_auction_only_images_policy.py','self.assertEqual(pub["lot_count"], 182)','self.assertEqual(pub["lot_count"], 232)\n            archived2=json.loads((ROOT / "'+manifest_path+'").read_text(encoding="utf-8"))["lots"]\n            ids2={r["id"] for r in archived2}\n            self.assertEqual(len(ids2),50)\n            self.assertEqual(sum(lot["id"] in ids2 and lot["rights_confirmed"] is False and lot["status"]=="reference_only" and len(lot["photos"])==2 for lot in pub["lots"]),50)')
replace('tests/test_site_warm_theme.py','self.assertEqual(lots["lot_count"],182)','self.assertEqual(lots["lot_count"],232)')
for path in ['AGENTS.md','docs/AUCTION_ONLY_GALLERY.md']:
    p=R/path;p.write_text(p.read_text()+'\nOwner instruction 2026-11-19, second batch: exactly the 50 cards in '+manifest_path+' approved after PDF/JPG presentation. No general release exception and no third-party license assertion. Keep all original photo, sheet and no-street-photo safeguards.\n')
print('Exact 50 second-batch records and 150 originals verified; 232 total release contract')
