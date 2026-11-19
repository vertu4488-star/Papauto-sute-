"""Build only the owner's exact second 50-card selection; verify reviewed source media bytes."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from urllib.parse import urlsplit
import hashlib,io,json,re
import requests
from PIL import Image
import pillow_avif

root=Path.cwd()
research=root/'research/next-50-20261119'
receipt=json.loads((research/'owner-exact-approval.json').read_text())
assert receipt['approved_count']==50 and receipt['owner_authorized_archival_reference_only'] is True
assert receipt['rights_confirmed'] is False
assert receipt['reviewed_pdf_sha256']=='8f9f0e37d605e5f4faced72994f4c9e246c02d886b213a379dfcd3acd18ac9bc'
assert receipt['raw_media_aggregate_sha256']=='53d5b85abd81282fb0e37e169617da7a08eb7562a5f77d35ab127e073432065b'
ids=receipt['source_uuids']
assert len(ids)==len(set(ids))==50
all_rows={}
for p in sorted(research.glob('part-*.json')):
    for x in json.loads(p.read_text()):
        uuid=x['source'].strip('/').split('/')[-1]
        if uuid in ids:
            if uuid in all_rows:assert all_rows[uuid]==x,uuid
            all_rows[uuid]=x
rows=[all_rows[u] for u in ids]
def sha(b):return hashlib.sha256(b).hexdigest()
fields=['model','year','num','date','price','spec','auction','source','source_status','conflicting_sale_status']
meta=[{**{k:x[k] for k in fields},'urls':x['urls'][:3]} for x in rows]
assert sha(json.dumps(meta,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())=='6813f508d196fca19e103d12ee7175ecd2f5cb3e28eea17595482bcb66da123b','approved metadata differs'
def key(x):
    a=re.sub('[^a-z0-9]','',x['auction'].lower())
    d=x.get('auction_date',x.get('date'))
    if '.' in d:d=datetime.strptime(d,'%d.%m.%Y').date().isoformat()
    return a,d,str(x.get('lot',x.get('lot_number',x.get('num')))).lstrip('0')
old=[]
for name in ['research/owner-selected-japan-lots-2026-11-14.json','research/owner-approved-50-archive-2026-11-19.json','data/gallery-lots.json']:
    old.extend(json.loads((root/name).read_text())['lots'])
assert not {key(x) for x in old}&{key(x) for x in rows}
assert len({key(x) for x in rows})==50
assert not {x.get('source_listing') for x in old}&{x['source'] for x in rows}
assets=root/'assets/auction/approved'
existing_hashes={sha(p.read_bytes()) for p in assets.iterdir() if p.is_file()}
def prepare(pair):
    i,x=pair
    assert x['source_status']=='archive displays sold' and x['conflicting_sale_status'] is False
    assert len(x['urls'])>=3 and len(set(x['urls'][:3]))==3
    assert not any(s in x['auction'].lower() for s in ['stock','oneprice','one price','quick','ippatsu'])
    ident=f'japan-archive-20261119-b2-{i:02d}'
    raw=[];med=[]
    for kind,idx in [('sheet',0),('front',1),('rear',2)]:
        url=x['urls'][idx]
        assert urlsplit(url).hostname=='japan.storage.yandexcloud.net' and x['source'].strip('/').split('/')[-1] in url
        res=requests.get(url,timeout=25);res.raise_for_status()
        raw.append(sha(res.content))
        im=Image.open(io.BytesIO(res.content)).convert('RGB');assert min(im.size)>=180
        b=io.BytesIO();im.save(b,'JPEG',quality=96,subsampling=0)
        data=b.getvalue();med.append((f'{ident}-{kind}.jpg',data,sha(data)))
    med=[med[1],med[2],med[0]]
    sp=x['spec'];cc=int(re.search(r'\d+',sp['Объем:'])[0]);assert 0<cc<=2000
    km=int(re.sub(r'\D','',sp['Пробег:']))
    assert sp['Оценка:'] in {'4.5','5'}
    amount=int(re.sub(r'\D','',x['price']));assert amount>0
    make,model=x['model'].split(' ',1)
    trim=sp.get('Комплектация:','').replace('\\*','*')
    hp=re.search(r'\d+',sp.get('Мощность:',''))
    desc=f"{x['model']} {x['year']} года, кузов {sp['Кузов:']}, комплектация {trim}, двигатель {cc} см³ ({sp.get('Двигатель:','—')}), КПП {sp.get('КПП:','—')}. Пробег {km} км, оценка {sp['Оценка:']}, аукцион {x['auction']}, {x['date']}, лот №{x['num']}. Статистика продаж на аукционах Японии. Автомобиль не в наличии и не предложение о продаже. Цена по данным аукциона, без доставки и оформления."
    row=dict(id=ident,country='japan',make=make,model=model,year=int(x['year']),mileage_km=km,body=sp['Кузов:'],grade=sp['Оценка:'],auction=x['auction'],lot=x['num'],auction_date=datetime.strptime(x['date'],'%d.%m.%Y').date().isoformat(),description=desc,photo_context='original_auction_lot',sheet_type='original_auction_sheet',photos=['/assets/auction/approved/'+m[0] for m in med[:2]],auction_sheet='/assets/auction/approved/'+med[2][0],sale_status='reference_only',reported_price=amount,media_sha256=[m[2] for m in med],source_listing=x['source'],source_media=[x['urls'][j] for j in [1,2,0]],raw_sha256=raw,trim=trim,engine_cc=cc,power_hp=int(hp[0]) if hp else None,rights_confirmed=False,reviewed_pdf_page=i)
    return row,med,raw
with ThreadPoolExecutor(max_workers=8) as p:
    built=list(p.map(prepare,enumerate(rows,1)))
records=[x[0] for x in built]
raw=[h for x in built for h in x[2]]
assert len(set(raw))==150 and sha(''.join(raw).encode())==receipt['raw_media_aggregate_sha256'],'review media bytes mismatch'
new_hashes=[h for x in records for h in x['media_sha256']]
assert len(set(new_hashes))==150 and not set(new_hashes)&existing_hashes
print('Verified exact 50 reviewed lots; all 150 source image hashes match; no historical duplicate keys',flush=True)
for _,media,_ in built:
    for name,b,_ in media:(assets/name).write_bytes(b)
new_rel='research/owner-approved-50-archive-batch2-2026-11-19.json'
manifest=dict(approval_date=receipt['approval_date'],approved_count=50,reviewed_pdf_sha256=receipt['reviewed_pdf_sha256'],raw_media_aggregate_sha256=receipt['raw_media_aggregate_sha256'],reviewed_metadata_sha256='6813f508d196fca19e103d12ee7175ecd2f5cb3e28eea17595482bcb66da123b',owner_authorized_archival_reference_only=True,rights_confirmed=False,rights_note='Exact owner-reviewed archive selection only. Owner approval is not third-party rights-holder consent.',lots=records)
(root/new_rel).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
def replace(path,a,b):
    p=root/path;s=p.read_text();assert s.count(a)==1,(path,a,s.count(a));p.write_text(s.replace(a,b,1))
def blob_id(p):
    b=(root/p).read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
patch='''        # Third exact reviewed batch; no general import authorization.
        next_receipt = json.loads((ROOT / "research/owner-approved-50-archive-batch2-2026-11-19.json").read_text(encoding="utf-8"))
        next_rows = next_receipt["lots"]
        if (next_receipt.get("approved_count") != 50
                or next_receipt.get("rights_confirmed") is not False
                or next_receipt.get("owner_authorized_archival_reference_only") is not True
                or next_receipt.get("reviewed_pdf_sha256") != "8f9f0e37d605e5f4faced72994f4c9e246c02d886b213a379dfcd3acd18ac9bc"
                or next_receipt.get("raw_media_aggregate_sha256") != "53d5b85abd81282fb0e37e169617da7a08eb7562a5f77d35ab127e073432065b"
                or [r["id"] for r in next_rows] != [f"japan-archive-20261119-b2-{i:02d}" for i in range(1,51)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in next_rows)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: second 50-card archive receipt mismatch")
        next_hashes = [h for r in next_rows for h in r["media_sha256"]]
        if len(next_hashes) != 150 or len(set(next_hashes + hashes + media_hashes)) != 494:
            raise RuntimeError("PAPAUTO_POLICY: duplicate reviewed media")
        for rec in next_rows:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
'''
replace('scripts/compile_auction_gallery.py','            additional.append(card)\n    seen_lot_keys','            additional.append(card)\n'+patch+'    seen_lot_keys')
replace('scripts/build_static_public.py','gallery_result["count"] != 182 or gallery_result["new"] != 147','gallery_result["count"] != 232 or gallery_result["new"] != 197')
replace('scripts/build_static_public.py','if published_lot_count != 182 or not lot_sitemap.is_file():','if published_lot_count != 232 or not lot_sitemap.is_file():')
replace('scripts/verify_publication_approval.py','FROZEN_SOURCE_BLOBS = {','FROZEN_SOURCE_BLOBS = {\n    "'+new_rel+'": "'+blob_id(new_rel)+'",')
replace('scripts/verify_publication_approval.py','    if (len(rows) != 182 or len(approved_archive) != 50 or len(approved_new) != 97 or len(approved_old) != 3','    next_archive = json.loads((ROOT / "'+new_rel+'").read_text(encoding="utf-8"))\n    next_ids = {r["id"] for r in next_archive["lots"]}\n    if (len(rows) != 232 or len(approved_archive) != 50 or len(next_ids) != 50 or len(approved_new) != 97 or len(approved_old) != 3')
replace('scripts/verify_publication_approval.py','not (approved_new | approved_old | approved_archive).issubset','not (approved_new | approved_old | approved_archive | next_ids).issubset')
replace('scripts/verify_publication_approval.py','!= (approved_new | approved_archive)):','!= (approved_new | approved_archive | next_ids)):')
replace('scripts/verify_publication_approval.py','if ident in approved_archive and','if ident in (approved_archive | next_ids) and')
replace('scripts/publish_lot_search.py','182 аукционных лота из Японии','232 аукционных лота из Японии')
replace('scripts/publish_lot_search.py','182 опубликованных примера','232 опубликованных примера')
replace('scripts/publish_lot_search.py','Все 182 аукционных лота','Все 232 аукционных лота')
replace('tests/test_auction_only_images_policy.py','self.assertEqual(pub["lot_count"], 182)','self.assertEqual(pub["lot_count"], 232)\n            second=json.loads((ROOT / "'+new_rel+'").read_text(encoding="utf-8"))["lots"]\n            second_ids={r["id"] for r in second}\n            self.assertEqual(len(second_ids),50)\n            self.assertEqual(sum(lot["id"] in second_ids and lot["rights_confirmed"] is False and lot["status"]=="reference_only" and len(lot["photos"])==2 for lot in pub["lots"]),50)')
replace('tests/test_site_warm_theme.py','self.assertEqual(lots["lot_count"],182)','self.assertEqual(lots["lot_count"],232)')
for path in ['AGENTS.md','docs/AUCTION_ONLY_GALLERY.md']:
    p=root/path
    p.write_text(p.read_text()+'\nOwner instruction 2026-11-19: exact second 50-card selection in '+new_rel+' was specifically authorized for archival sales statistics after review. No broader rights assertion; rights_confirmed remains false, original media and all quality protections remain mandatory.\n')
print('Prepared 232-card publication contract.',flush=True)
