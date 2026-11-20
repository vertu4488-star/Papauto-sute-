import hashlib,html,json,re,sys
from pathlib import Path
from urllib.parse import quote
from verify_china_order_release import verify

P=Path
assert len(verify())==229
review=json.loads(P('research/china-next30-review-2026-11-20.json').read_text())
rows=review['records'];assert len(rows)==30
assert len({x['photo_sha256'] for x in rows})==30
old=[]
for batch in ('49','30','third30','fourth30','fifth30','160hp30','160hp11','160hp10','goldenlane9'):
    old+=json.loads(P(f'research/owner-approved-china-supplier-{batch}-2026-11-20.json').read_text())['records']
assert len(old)==229
urls={r['photo_url'] for r in old};hashes={r['photo_sha256'] for r in old}
sources={r.get('source') for r in old}
prefix='assets/china-order/owner-20261120-next30/'
P(prefix).mkdir(parents=True,exist_ok=False)
groups={'china':'Китайские марки','japan':'Японские марки','usa':'Американские марки','europe':'Европейские марки','korea':'Корейские марки'}
brands={'mazda':'japan','toyota':'japan','nissan':'japan','honda':'japan','mitsubishi':'japan','suzuki':'japan','subaru':'japan','kia':'korea','hyundai':'korea','volkswagen':'europe','vw':'europe','jetta':'europe','skoda':'europe','škoda':'europe','audi':'europe','bmw':'europe','mercedes':'europe','mercedes-benz':'europe','mini':'europe','volvo':'europe','peugeot':'europe','citroen':'europe','mg':'china','geely':'china','chery':'china','haval':'china','harvard':'china','changan':'china','gac':'china','jetour':'china','dongfeng':'china','roewe':'china','wuling':'china','byd':'china','chevrolet':'usa','ford':'usa','buick':'usa'}
cards=[];receipt=[];new={};counts={'GoldenLane Auto':0,'EZ Auto Global':0}
for i,ref in enumerate(rows,230):
    folder=P('/tmp/china259')/str(ref['artifact_id'])
    archive={x['id']:x for x in json.loads((folder/'manifest.json').read_text())['records']}
    r=dict(archive[ref['artifact_record_id']])
    assert r['photo_url']==ref['photo_url'] and r['source']==ref['source'], ('source mismatch',ref)
    assert r['photo_url'] not in urls
    if 'goldenlaneauto.com' in r['source']:
        assert r['source'] not in sources
        source_name='GoldenLane Auto'
        currency='CNY';price=r['price_cny']
        assert 0<float(r['power_kw_listed'])<=117.68
    else:
        assert r['source']=='https://ezautoglobal.com/en/cars'
        source_name='EZ Auto Global'
        currency='USD';price=r['price_usd']
        vehicle_id=r['photo_url'].split('/')[5]
        assert not any('/'+vehicle_id+'/' in u for u in urls)
    counts[source_name]+=1
    hp=r['power_ps_listed']
    assert 0<hp<=160, r
    assert float(re.search(r'\d\.\d',r['engine']).group())<=2
    assert isinstance(r['mileage_km'],int) and r['mileage_km']>=0 and price>0
    src=folder/(ref['artifact_record_id']+'.jpg');b=src.read_bytes()
    digest=hashlib.sha256(b).hexdigest()
    assert digest==ref['photo_sha256'] and digest not in hashes and b.startswith(b'\xff\xd8\xff') and len(b)>500,ref
    ident=str(i-229).zfill(3);new[ident]=digest
    path=prefix+ident+'.jpg';P(path).write_bytes(b)
    name=html.unescape(r['title']).strip()+' · '+str(r['year'])
    origin=brands[name.split()[0].casefold()]
    e=html.escape;link='/podbor.html?similar='+quote(name+' · КИТАЙ')
    cards.append(f'<article class="cn-example" data-origin="{origin}" data-power="{hp}" data-search="{e(name+" "+r["engine"],quote=True)}"><div class="cn-overline">{groups[origin]} · {i} / 259</div><img src="/{path}" alt="{e(name,quote=True)}" loading="lazy" decoding="async" width="1000" height="750"><div class="cn-body"><h2>{e(name)}</h2><dl><div><dt>Двигатель</dt><dd>{e(r["engine"])}</dd></div><div><dt>Мощность по объявлению</dt><dd>{hp} л.с.</dd></div><div><dt>Пробег по данным поставщика</dt><dd>{r["mileage_km"]:,} км</dd></div><div><dt>Начальная цена поставщика (условия уточняются)</dt><dd>от {price:,} {currency}</dd></div></dl><p>Пример подбора. Условия поставки и состав цены уточняются; мощность по документам и льготный утильсбор не подтверждены.</p><a class="button button-primary" href="{link}">Подобрать аналог</a></div></article>')
    receipt.append(dict(r,artifact_id=ref['artifact_id'],source_run_id=ref['source_run_id'],artifact_record_id=ref['artifact_record_id'],photo_path='/'+path,photo_sha256=digest,brand_group=origin,publication_approved=True,rights_confirmed=False,documented_power_kw=None,inspection_report=None,status='supplier_reference_only'))
    hashes.add(digest);urls.add(r['photo_url']);sources.add(r['source'])
assert counts=={'GoldenLane Auto':19,'EZ Auto Global':11}
v=P('scripts/verify_china_order_release.py');s=v.read_text()
s=s.replace('def verify(root=ROOT):','TENTH_PREFIX = '+repr(prefix)+'\nTENTH_HASHES = '+repr(new)+'\n\ndef verify(root=ROOT):')
needle=' | {NINTH_PREFIX + ident + ".jpg" for ident in NINTH_HASHES}'
assert s.count(needle)==1
s=s.replace(needle,needle+' | {TENTH_PREFIX + ident + ".jpg" for ident in TENTH_HASHES}')
needle='    html = (root/PAGE).read_text(encoding="utf-8")'
assert s.count(needle)==1
s=s.replace(needle,'    for ident, digest in TENTH_HASHES.items():\n        p = root / TENTH_PREFIX / (ident + ".jpg")\n        b = p.read_bytes()\n        if p.is_symlink() or len(b)<500 or not b.startswith(b"\\xff\\xd8\\xff") or hashlib.sha256(b).hexdigest()!=digest:\n            raise RuntimeError("CHINA_ORDER: approved thirty photo mismatch " + ident)\n'+needle)
needle=' + ["/"+NINTH_PREFIX+i+".jpg" for i in NINTH_HASHES]'
assert s.count(needle)==1
s=s.replace(needle,needle+' + ["/"+TENTH_PREFIX+i+".jpg" for i in TENTH_HASHES]')
v.write_text(s)
p=P('china-order.html');page=p.read_text()
assert page.count('class="cn-example"')==229
page=page.replace('229 примеров','259 примеров')
page=re.sub(r'(· \d{2,3} / )229</div>',r'\g<1>259</div>',page)
needle='</div><p><a href="/china-util-models.html">'
assert page.count(needle)==1
p.write_text(page.replace(needle,''.join(cards)+needle))
assert p.read_text().count('class="cn-example"')==259
p=P('china.html');s=p.read_text();assert '229 автомобилей с фотографиями' in s;p.write_text(s.replace('229 автомобилей с фотографиями','259 автомобилей с фотографиями'))
P('research/owner-approved-china-supplier-next30-2026-11-20.json').write_text(json.dumps({'owner_approval':'2026-11-20: expressly approved all exact thirty cards in PapAuto_30_China_review.pdf','third_party_license_verified':False,'auction_lots':False,'records':receipt},ensure_ascii=False,indent=2)+'\n')
for f in ('AGENTS.md','docs/AUCTION_ONLY_GALLERY.md'):
    p=P(f);p.write_text(p.read_text().rstrip()+'\n\nOwner instruction 2026-11-20: exact 30 supplier examples shown in PapAuto_30_China_review.pdf expressly approved for china-order.html. Only fixed tenth-batch digests permitted, 19 GoldenLane and 11 EZ Auto Global. No license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.\n')
p=P('research/CHINA_SUPPLIER_SOURCE_REGISTER.md');p.write_text(p.read_text().rstrip()+'\n\nTenth approved batch: research/owner-approved-china-supplier-next30-2026-11-20.json; 19 GoldenLane and 11 EZ Auto Global (38 GoldenLane, 50 EZ, 259 overall). Exact archive IDs, supplier URLs, prices and local photo SHA-256 preserved.\n')
print('259 cards assembled; all thirty exact approved images preserved byte-for-byte.')
