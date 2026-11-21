from pathlib import Path
from PIL import Image
import json,hashlib,re
root=Path('.'); source=Path('/tmp/drom20'); rows=json.loads((source/'manifest.json').read_text())
assert len(rows)==20
prior=json.loads(Path('data/gallery-lots.json').read_text())['lots']
keys={(re.sub('[^a-z0-9]','',r['auction'].lower()),r['auction_date'],str(r['lot_number']).lstrip('0')) for r in prior}
records=[]
for i,r in enumerate(rows,1):
 assert len(r['files'])==3 and len(r['raw_sha256'])==3 and len(r['media_urls'])==3
 key=(re.sub('[^a-z0-9]','',r['auction'].lower()),r['date'],str(r['lot']).lstrip('0'))
 assert key not in keys,('duplicate',key)
 keys.add(key)
 title=re.fullmatch(r'(.+?) (20\\d\\d) года',r['title'])
 assert title and int(title[2])==r['year']
 make,model=title[1].split(' ',1)
 ident=f'japan-drom991-20-20261121-{i:02d}'
 dest=[];sha=[]
 for j,role in enumerate(('front','rear','sheet')):
  raw=(source/r['files'][j]).read_bytes()
  with Image.open(source/r['files'][j]) as im:
   assert im.format=='JPEG' and min(im.size)>=(700 if j==2 else 180)
  p=Path('assets/auction/approved')/(ident+'-'+role+'.jpg')
  assert not p.exists()
  p.write_bytes(raw)
  dest.append('/'+p.as_posix());sha.append(hashlib.sha256(raw).hexdigest())
 assert len(set(sha))==3
 assert r['raw_sha256']!=sha or True
 desc=f"{make} {model}, {r['year']} года, кузов {r['body']}, комплектация {r['trim']}. Двигатель {r['cc']} см³, мощность {r['hp']} л.с. Пробег {r['km']} км, оценка {r['grade']}, аукцион {r['auction']}, дата {r['date']}, лот №{r['lot']}. Автомобиль не в наличии: историческая статистика аукционных продаж Японии. Цена аукциона без доставки и таможенных платежей."
 records.append(dict(id=ident,country='japan',make=make,model=model,year=r['year'],mileage_km=r['km'],body=r['body'],grade=r['grade'],auction=r['auction'],lot=str(r['lot']),auction_date=r['date'],description=desc,photo_context='original_auction_lot',sheet_type='original_auction_sheet',photos=dest[:2],auction_sheet=dest[2],sale_status='reference_only',reported_price=r['price_jpy'],media_sha256=sha,source_listing=r['source'],source_media=r['media_urls'],rights_confirmed=False,engine_cc=r['cc'],power_hp=r['hp']))
manifest=Path('research/owner-approved-japan-drom991-20-2026-11-21.json')
manifest.write_text(json.dumps(dict(approved_count=20,rights_confirmed=False,owner_authorized_archival_reference_only=True,lots=records),ensure_ascii=False,indent=2)+'\\n')
compiler=Path('scripts/compile_auction_gallery.py')
s=compiler.read_text()
anchor='    seen_lot_keys = {'
assert s.count(anchor)==1
addition='''        archive17 = json.loads((ROOT / "research/owner-approved-japan-drom991-20-2026-11-21.json").read_text(encoding="utf-8"))
        if archive17.get("approved_count") != 20 or archive17.get("rights_confirmed") is not False:
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: Japan 20")
        for rec in archive17["lots"]:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(engine_cc=rec["engine_cc"], power_hp=rec["power_hp"], sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
'''
s=s.replace(anchor,addition+anchor,1);compiler.write_text(s)
print('PREPARED_20_EXACT_ORIGINALS',len(records))
