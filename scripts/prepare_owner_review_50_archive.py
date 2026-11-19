"""Prepare the EXACT owner-authorized archival reference set. No general permission inferred."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import hashlib, io, json, re
from urllib.parse import urlsplit
import requests
from PIL import Image
import pillow_avif

ROOT=Path.cwd()
research=ROOT/'research/review-50-tokidoki'
approval=json.loads((research/'owner-approval-2026-11-19.json').read_text())
assert approval['approved_count']==50 and approval['no_other_media_exception'] is True
assert approval['rights_confirmed'] is False
assert approval['reviewed_pdf_sha256']=='7c4c0c775dbcf3f4ca6f8f967282d66e6692f147b02d4ce74b67bcdb614746a6'
rows=approval['lots']
assert [x['page'] for x in rows]==list(range(1,51))
facts={x['lot']:x for p in sorted(research.glob('auction-facts-*.json')) for x in json.loads(p.read_text())}
fp={x.split()[0]:[int(i,16) for i in x.split()[1:]] for x in (research/'reviewed-image-fingerprints.txt').read_text().splitlines() if x}
assert len(rows)==len(facts)==len(fp)==50
assert len({x['lot'] for x in rows})==50
assets=ROOT/'assets/auction/approved'
def digest(data):return hashlib.sha256(data).hexdigest()
def dhash(im):
    px=list(im.convert('L').resize((9,8),Image.Resampling.LANCZOS).getdata())
    acc=0
    for y in range(8):
        for x in range(8): acc=(acc<<1)|int(px[y*9+x+1]>px[y*9+x])
    return acc
def prepare(x):
    lot=x['lot']; f=facts[lot]
    assert f['source']==x['source_listing'] and f['status']=='archive_sold_displayed'
    assert f['auction'] and len(x['source_gallery'])>=3
    ident=f"japan-archive-20261119-{int(x['page']):02d}"
    media=[]
    for kind,idx,n in [('front',1,0),('rear',2,1),('sheet',0,2)]:
        url=x['source_gallery'][idx]
        assert urlsplit(url).hostname=='japan.storage.yandexcloud.net' and x['source_listing'].strip('/').split('/')[-1] in url
        response=requests.get(url,timeout=25)
        response.raise_for_status()
        im=Image.open(io.BytesIO(response.content)).convert('RGB')
        assert min(im.size)>=180
        distance=(dhash(im)^fp[lot][n]).bit_count()
        assert distance<=5, f"REVIEWED IMAGE MISMATCH {lot} {kind} {distance}"
        name=f'{ident}-{kind}.jpg'; buf=io.BytesIO(); im.save(buf,format='JPEG',quality=96,subsampling=0)
        data=buf.getvalue()
        media.append((name,data,digest(data)))
    spec=x['spec']; make,model=x['model'].split(' ',1)
    km=int(re.sub(r'\D','',spec['Пробег:']))
    cc=int(re.search(r'\d+',spec['Объем:'])[0]);assert cc<=2000
    amount=int(re.sub(r'\D','',x['reported_price']))
    trim=spec.get('Комплектация:','').replace('\\*','*')
    desc=f"{x['model']} {x['year']} года, кузов {spec['Кузов:']}, комплектация {trim}, двигатель {cc} см³ ({spec.get('Двигатель:','—')}), КПП {spec.get('КПП:','—')}. Пробег {km:,} км, оценка {spec['Оценка:']}, аукцион {f['auction']}, {x['auction_date']}, лот №{lot}. Архивный пример для ознакомления: автомобиль не в наличии и не предлагается к продаже. Историческая цена в Японии по данным архива ТокиДоки, без доставки и оформления.".replace(',', ' ',1) if False else f"{x['model']} {x['year']} года, кузов {spec['Кузов:']}, комплектация {trim}, двигатель {cc} см³ ({spec.get('Двигатель:','—')}), КПП {spec.get('КПП:','—')}. Пробег {km} км, оценка {spec['Оценка:']}, аукцион {f['auction']}, {x['auction_date']}, лот №{lot}. Архивный пример для ознакомления, не автомобиль в наличии и не предложение о продаже. Историческая цена в Японии по данным архива ТокиДоки, без доставки и оформления."
    record=dict(id=ident,country='japan',make=make,model=model,year=int(x['year']),mileage_km=km,body=spec['Кузов:'],grade=spec['Оценка:'],auction=f['auction'],lot=lot,auction_date=datetime.strptime(x['auction_date'],'%d.%m.%Y').date().isoformat(),description=desc,photo_context='original_auction_lot',sheet_type='original_auction_sheet',photos=['/assets/auction/approved/'+t[0] for t in media[:2]],auction_sheet='/assets/auction/approved/'+media[2][0],sale_status='reference_only',reported_price=amount,media_sha256=[t[2] for t in media],source_listing=x['source_listing'],source_media=[x['source_gallery'][i] for i in [1,2,0]],trim=trim,engine_cc=cc,power_hp=int(re.search(r'\d+',spec['Мощность:'])[0]) if re.search(r'\d+',spec.get('Мощность:','')) else None,rights_confirmed=False,reviewed_pdf_page=x['page'])
    return record,media

with ThreadPoolExecutor(max_workers=6) as pool: built=list(pool.map(prepare,rows))
records=[x[0] for x in built]
all_digests=[d for row in records for d in row['media_sha256']]
assert len(set(all_digests))==150
old=json.loads((ROOT/'research/owner-selected-japan-lots-2026-11-14.json').read_text())['lots']
base=json.loads((ROOT/'data/gallery-lots.json').read_text())['lots']
keys={(x['auction'],x['auction_date'],str(x.get('lot',x.get('lot_number')))) for x in old+base}
assert not keys & {(x['auction'],x['auction_date'],x['lot']) for x in records}
assert not set(all_digests)&{d for x in old for d in x.get('media_sha256',[])}
for old_path in assets.glob('*'):
    if old_path.is_file() and digest(old_path.read_bytes()) in all_digests: raise RuntimeError('duplicate historical media')
for record,media in built:
    for name,data,_ in media: (assets/name).write_bytes(data)
new_rel='research/owner-approved-50-archive-2026-11-19.json'
manifest=dict(approval_date='2026-11-19',approved_count=50,reviewed_pdf_sha256=approval['reviewed_pdf_sha256'],owner_authorized_archival_reference_only=True,rights_confirmed=False,rights_note='Owner authorization is not third-party rights-holder consent. No ordinary import rule changed.',lots=records)
(ROOT/new_rel).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
def replace(path,old,new):
    p=ROOT/path;s=p.read_text(); assert s.count(old)==1, (path,old,s.count(old));p.write_text(s.replace(old,new,1))
def blob_id(p):
    b=(ROOT/p).read_bytes()
    return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
patch='''        # Exact second owner-authorized archival release; no general import permission.
        archive = json.loads((ROOT / "research/owner-approved-50-archive-2026-11-19.json").read_text(encoding="utf-8"))
        archived = archive["lots"]
        if (archive.get("approved_count") != 50 or archive.get("rights_confirmed") is not False
                or archive.get("owner_authorized_archival_reference_only") is not True
                or archive.get("reviewed_pdf_sha256") != "7c4c0c775dbcf3f4ca6f8f967282d66e6692f147b02d4ce74b67bcdb614746a6"
                or [r["id"] for r in archived] != [f"japan-archive-20261119-{i:02d}" for i in range(1,51)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: 50-card archive receipt mismatch")
        hashes = [h for r in archived for h in r["media_sha256"]]
        if len(hashes) != 150 or len(set(hashes + media_hashes)) != 344:
            raise RuntimeError("PAPAUTO_POLICY: duplicate reviewed media")
        for rec in archived:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Архивный пример, не в наличии", rights_confirmed=False)
            additional.append(card)
'''
replace('scripts/compile_auction_gallery.py','        additional.extend(prepare_approved(target, row, owner_selected=True) for row in selection)\n','        additional.extend(prepare_approved(target, row, owner_selected=True) for row in selection)\n'+patch)
replace('scripts/build_static_public.py','gallery_result["count"] != 132 or gallery_result["new"] != 97','gallery_result["count"] != 182 or gallery_result["new"] != 147')
replace('scripts/build_static_public.py','if published_lot_count != 132 or not lot_sitemap.is_file():','if published_lot_count != 182 or not lot_sitemap.is_file():')
replace('scripts/verify_publication_approval.py','FROZEN_SOURCE_BLOBS = {','FROZEN_SOURCE_BLOBS = {\n    "'+new_rel+'": "'+blob_id(new_rel)+'",')
replace('scripts/verify_publication_approval.py','    if (len(rows) != 132 or len(approved_new) != 97 or len(approved_old) != 3','    archive = json.loads((ROOT / "'+new_rel+'").read_text(encoding="utf-8"))\n    approved_archive = {r["id"] for r in archive["lots"]}\n    if (len(rows) != 182 or len(approved_archive) != 50 or len(approved_new) != 97 or len(approved_old) != 3')
replace('scripts/verify_publication_approval.py','not (approved_new | approved_old).issubset','not (approved_new | approved_old | approved_archive).issubset')
replace('scripts/verify_publication_approval.py','!= approved_new):','!= (approved_new | approved_archive)):' )
replace('scripts/verify_publication_approval.py','        if row.get("inspection_kind") != "Аукционный лист":','        if ident in approved_archive and (row.get("rights_confirmed") is not False or row.get("status") != "reference_only" or len(row.get("photos",[]))!=2 or "не автомобиль в наличии" not in row.get("description","")):\n            raise RuntimeError("PAPAUTO_POLICY: archive reference misrepresented: " + ident)\n        if row.get("inspection_kind") != "Аукционный лист":')
replace('scripts/publish_lot_search.py','132 аукционных лота из Японии','182 аукционных лота из Японии')
replace('scripts/publish_lot_search.py','132 опубликованных примера','182 опубликованных примера')
replace('scripts/publish_lot_search.py','Все 132 аукционных лота','Все 182 аукционных лота')
replace('tests/test_auction_only_images_policy.py','self.assertEqual(pub["lot_count"], 132)','self.assertEqual(pub["lot_count"], 182)\n            archived=json.loads((ROOT / "'+new_rel+'").read_text(encoding="utf-8"))["lots"]\n            archived_ids={r["id"] for r in archived}\n            self.assertEqual(len(archived_ids),50)\n            self.assertEqual(sum(lot["id"] in archived_ids and lot["rights_confirmed"] is False and lot["status"]=="reference_only" and len(lot["photos"])==2 for lot in pub["lots"]),50)')
for path in ['AGENTS.md','docs/AUCTION_ONLY_GALLERY.md']:
    p=ROOT/path
    p.write_text(p.read_text()+'\nOwner instruction 2026-11-19: exactly the 50 reviewed Japan archival reference records in '+new_rel+' were authorized explicitly under the owner’s responsibility. This is not a third-party license; rights_confirmed stays false. No general exception, no street or unrelated photos, no missing sheets, no external card links, and no available-for-sale claims. Ordinary importer rights requirements remain in force for any other batch.\n')
print('PAPAUTO exact 50 archival references, 150 media, all matched review; release contract updated for 182')
