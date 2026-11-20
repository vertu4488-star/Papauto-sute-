import hashlib,html,json,re,sys
from pathlib import Path
from urllib.parse import quote
from verify_china_order_release import verify

P=Path
assert len(verify())==469
review=json.loads(P('research/china-next30-batch18-review-2026-11-20.json').read_text())
rows=review['records'];assert len(rows)==30
assert len({x['photo_sha256'] for x in rows})==30
old=[]
for batch in ('49','30','third30','fourth30','fifth30','160hp30','160hp11','160hp10','goldenlane9','next30','batch11','batch12','batch13','batch14','batch15','batch16','batch17'):
    old+=json.loads(P(f'research/owner-approved-china-supplier-{batch}-2026-11-20.json').read_text())['records']
assert len(old)==469
urls={r['photo_url'] for r in old};hashes={r['photo_sha256'] for r in old}
sources={r.get('source') for r in old}
prefix='assets/china-order/owner-20261120-batch18/'
P(prefix).mkdir(parents=True,exist_ok=False)
groups={'china':'Китайские марки','japan':'Японские марки','usa':'Американские марки','europe':'Европейские марки','korea':'Корейские марки'}
brands={'mazda':'japan','toyota':'japan','nissan':'japan','honda':'japan','mitsubishi':'japan','suzuki':'japan','subaru':'japan','kia':'korea','hyundai':'korea','volkswagen':'europe','vw':'europe','jetta':'europe','skoda':'europe','škoda':'europe','audi':'europe','bmw':'europe','mercedes':'europe','mercedes-benz':'europe','mini':'europe','volvo':'europe','peugeot':'europe','citroen':'europe','mg':'china','geely':'china','chery':'china','haval':'china','harvard':'china','changan':'china','gac':'china','jetour':'china','dongfeng':'china','roewe':'china','wuling':'china','byd':'china','chevrolet':'usa','ford':'usa','buick':'usa'}
brands.update({'jaguar':'europe','land':'europe','land-rover':'europe','range':'europe','porsche':'europe','alfa':'europe','opel':'europe','renault':'europe','cadillac':'usa','lincoln':'usa','jeep':'usa','tesla':'usa','lexus':'japan','infiniti':'japan','acura':'japan','genesis':'korea','baic':'china','bestune':'china','hongqi':'china','maxus':'china','faw':'china','saic':'china','lynk':'china','exeed':'china','chery':'china','foton':'china','jac':'china','great':'china','leapmotor':'china','nio':'china','xpeng':'china','zeekr':'china','smart':'europe'})
brands.update({'baojun':'china','changan':'china','changhe':'china','soueast':'china','haima':'china','venucia':'china','dfsk':'china','lifan':'china','zotye':'china','kaiyi':'china','chery':'china','trumpchi':'china','jetour':'china','forthing':'china','sehol':'china','lancia':'europe','ds':'europe','seat':'europe','cupra':'europe','ssangyong':'korea','daihatsu':'japan','isuzu':'japan','dodge':'usa','chrysler':'usa'})
cards=[];receipt=[];new={};counts={'Xin Che Hang':0}
for i,ref in enumerate(rows,470):
    folder=P('/tmp/china499')/str(ref['artifact_id'])
    archive={x['id']:x for x in json.loads((folder/'manifest.json').read_text())['records']}
    r=dict(archive[ref['artifact_record_id']])
    assert r['photo_url']==ref['photo_url'] and r['source']==ref['source'], ('source mismatch',ref)
    assert r['photo_url'] not in urls
    assert r['source']=='https://www.xchehang.com/inventory.html'
    price=r['fob_usd']
    hp=None
    price_label='Цена FOB по данным поставщика'
    assert r.get('documented_power_kw') is None
    name=html.unescape(r['title']).strip()
    origin=r.get('brand_group') or brands[name.split()[1].casefold()]
    counts['Xin Che Hang']+=1
    currency='USD'
    assert origin in groups and r['engine'] and name, (ref['artifact_record_id'],name,origin,r['engine'])
    assert isinstance(r['mileage_km'],int) and r['mileage_km']>=0 and price>0
    src=folder/(ref['artifact_record_id']+'.jpg');b=src.read_bytes()
    digest=hashlib.sha256(b).hexdigest()
    assert digest==ref['photo_sha256'] and digest not in hashes and b.startswith(b'\xff\xd8\xff') and len(b)>500,ref
    ident=str(i-469).zfill(3);new[ident]=digest
    path=prefix+ident+'.jpg';P(path).write_bytes(b)
    power_attr=f' data-power="{hp}"' if hp is not None else ''
    power_value=f'{hp} л.с. (по объявлению)' if hp is not None else 'Требует уточнения'
    e=html.escape;link='/podbor.html?similar='+quote(name+' · КИТАЙ')
    cards.append(f'<article class="cn-example" data-origin="{origin}"{power_attr} data-search="{e(name+" "+r["engine"],quote=True)}"><div class="cn-overline">{groups[origin]} · {i} / 499</div><img src="/{path}" alt="{e(name,quote=True)}" loading="lazy" decoding="async" width="1000" height="750"><div class="cn-body"><h2>{e(name)}</h2><dl><div><dt>Двигатель</dt><dd>{e(r["engine"])}</dd></div><div><dt>Мощность</dt><dd>{power_value}</dd></div><div><dt>Пробег по данным поставщика</dt><dd>{r["mileage_km"]:,} км</dd></div><div><dt>{price_label}</dt><dd>{price:,} {currency}</dd></div></dl><p>Пример подбора. Условия поставки и состав цены уточняются; мощность по документам и льготный утильсбор не подтверждены.</p><a class="button button-primary" href="{link}">Подобрать аналог</a></div></article>')
    receipt.append(dict(r,artifact_id=ref['artifact_id'],source_run_id=ref['source_run_id'],artifact_record_id=ref['artifact_record_id'],photo_path='/'+path,photo_sha256=digest,brand_group=origin,power_ps_listed=hp,publication_approved=True,rights_confirmed=False,documented_power_kw=None,inspection_report=None,status='supplier_reference_only'))
    hashes.add(digest);urls.add(r['photo_url']);sources.add(r['source'])
assert counts=={'Xin Che Hang':30}
v=P('scripts/verify_china_order_release.py');s=v.read_text()
s=s.replace('def verify(root=ROOT):','EIGHTEENTH_PREFIX = '+repr(prefix)+'\nEIGHTEENTH_HASHES = '+repr(new)+'\n\ndef verify(root=ROOT):')
needle=' | {SEVENTEENTH_PREFIX + ident + ".jpg" for ident in SEVENTEENTH_HASHES}'
assert s.count(needle)==1
s=s.replace(needle,needle+' | {EIGHTEENTH_PREFIX + ident + ".jpg" for ident in EIGHTEENTH_HASHES}')
needle='    html = (root/PAGE).read_text(encoding="utf-8")'
assert s.count(needle)==1
s=s.replace(needle,'    for ident, digest in EIGHTEENTH_HASHES.items():\n        p = root / EIGHTEENTH_PREFIX / (ident + ".jpg")\n        b = p.read_bytes()\n        if p.is_symlink() or len(b)<500 or not b.startswith(b"\\xff\\xd8\\xff") or hashlib.sha256(b).hexdigest()!=digest:\n            raise RuntimeError("CHINA_ORDER: approved thirty photo mismatch " + ident)\n'+needle)
needle=' + ["/"+SEVENTEENTH_PREFIX+i+".jpg" for i in SEVENTEENTH_HASHES]'
assert s.count(needle)==1
s=s.replace(needle,needle+' + ["/"+EIGHTEENTH_PREFIX+i+".jpg" for i in EIGHTEENTH_HASHES]')
v.write_text(s)
p=P('china-order.html');page=p.read_text()
assert page.count('class="cn-example"')==469
page=page.replace('469 примеров','499 примеров')
page=re.sub(r'(· \d{2,3} / )469</div>',r'\g<1>499</div>',page)
needle='</div><p><a href="/china-util-models.html">'
assert page.count(needle)==1
p.write_text(page.replace(needle,''.join(cards)+needle))
assert p.read_text().count('class="cn-example"')==499
p=P('china.html');s=p.read_text();assert '469 автомобилей с фотографиями' in s;p.write_text(s.replace('469 автомобилей с фотографиями','499 автомобилей с фотографиями'))
P('research/owner-approved-china-supplier-batch18-2026-11-20.json').write_text(json.dumps({'owner_approval':'2026-11-20: expressly approved all exact thirty cards in PapAuto_China_30_batch18.pdf','third_party_license_verified':False,'auction_lots':False,'records':receipt},ensure_ascii=False,indent=2)+'\n')
for f in ('AGENTS.md','docs/AUCTION_ONLY_GALLERY.md'):
    p=P(f);p.write_text(p.read_text().rstrip()+'\n\nOwner instruction 2026-11-20: exact 30 supplier examples shown in PapAuto_China_30_batch18.pdf expressly approved for china-order.html. Only fixed eighteenth-batch digests permitted, 30 Xin Che Hang. No license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.\n')
p=P('research/CHINA_SUPPLIER_SOURCE_REGISTER.md');p.write_text(p.read_text().rstrip()+'\n\nEighteenth approved batch: research/owner-approved-china-supplier-batch18-2026-11-20.json; 30 Xin Che Hang (406 Xin Che Hang, 4 China Used Car, 38 GoldenLane, 50 EZ, 1 other, 499 overall). Exact archive IDs, supplier URLs, prices and local photo SHA-256 preserved.\n')
print('499 cards assembled; all thirty exact approved images preserved byte-for-byte.')
