import hashlib, html, json, re, shutil, sys
from pathlib import Path
from urllib.parse import quote
from verify_china_order_release import SEVENTH_HASHES, SEVENTH_PREFIX, verify

archive=Path(sys.argv[1])
by={r['id']:r for r in json.loads((archive/'manifest.json').read_text())['records']}
old=[]
for batch in ('49','30','third30','fourth30','fifth30','160hp30'):
    old+=json.loads(Path(f'research/owner-approved-china-supplier-{batch}-2026-11-20.json').read_text())['records']
assert len(old)==199 and len(SEVENTH_HASHES)==11
seen_urls={r['photo_url'] for r in old}
seen_hashes={r['photo_sha256'] for r in old}
media=Path(SEVENTH_PREFIX);media.mkdir(parents=True,exist_ok=True)
groups={'china':'Китайские марки','japan':'Японские марки','usa':'Американские марки','europe':'Европейские марки','korea':'Корейские марки'}
brands={'mazda':'japan','toyota':'japan','nissan':'japan','honda':'japan','mitsubishi':'japan','suzuki':'japan','subaru':'japan','kia':'korea','hyundai':'korea','volkswagen':'europe','vw':'europe','jetta':'europe','skoda':'europe','škoda':'europe','audi':'europe','bmw':'europe','mercedes':'europe','mercedes-benz':'europe','mini':'europe','volvo':'europe','peugeot':'europe','citroen':'europe','mg':'china','geely':'china','chery':'china','haval':'china','changan':'china','gac':'china','jetour':'china','dongfeng':'china','roewe':'china','wuling':'china','byd':'china','chevrolet':'usa','ford':'usa','buick':'usa'}
powers={'006':155,'026':150,'034':150,'039':130,'050':110,'051':150,'052':150,'055':149,'063':150,'001':150,'002':150}
e=html.escape;cards=[];receipt=[]
for num,(ident,digest) in enumerate(SEVENTH_HASHES.items(),200):
    dealer=ident in ('001','002')
    source_archive=Path(sys.argv[2]) if dealer else archive
    source_run=44693561445 if dealer else 44699371077
    r=dict({x['id']:x for x in json.loads((source_archive/'manifest.json').read_text())['records']}[ident])
    if dealer:
        r['power_ps_listed']=int(re.search(r'(\d+)PS',r['engine']).group(1))
        assert r['power_kw_listed']<=117.68
    hp=r['power_ps_listed']
    assert hp==powers[ident] and 0<hp<=160
    assert float(re.search(r'\d\.\d',r['engine']).group())<=2
    assert r['photo_url'] not in seen_urls and digest not in seen_hashes
    assert isinstance(r['mileage_km'],int) and r['mileage_km']>=0 and r['price_usd']>0
    src=source_archive/(ident+'.jpg')
    assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
    img=media/(ident+'.jpg');shutil.copyfile(src,img)
    model=html.unescape(r['title']).strip()
    origin=brands[model.split()[0].casefold()]
    seen_urls.add(r['photo_url']);seen_hashes.add(digest)
    name=model if dealer else model+' · '+str(r['year'])
    price_label='Цена FOB по объявлению' if dealer else 'Цена поставщика от 20.11.2026'
    price_prefix='' if dealer else 'от '
    r['price_type']='supplier FOB' if dealer else 'supplier starting price; trade terms unspecified'
    receipt.append(dict(r,artifact_record_id=ident,photo_sha256=digest,source_run_id=source_run,photo_path='/'+img.as_posix(),brand_group=origin,publication_approved=True,rights_confirmed=False,documented_power_kw=None,inspection_report=None,status='supplier_reference_only'))
    url='/podbor.html?similar='+quote(name+' · КИТАЙ')
    cards.append(f'<article class="cn-example" data-origin="{origin}" data-power="{hp}" data-search="{e(name+" "+r["engine"],quote=True)}"><div class="cn-overline">{groups[origin]} · {num} / 210</div><img src="/{img.as_posix()}" alt="{e(name,quote=True)}" loading="lazy" decoding="async" width="1000" height="750"><div class="cn-body"><h2>{e(name)}</h2><dl><div><dt>Двигатель</dt><dd>{e(r["engine"])}</dd></div><div><dt>Мощность по объявлению</dt><dd>{hp} л.с.</dd></div><div><dt>Пробег по данным поставщика</dt><dd>{r["mileage_km"]:,} км</dd></div><div><dt>{price_label}</dt><dd>{price_prefix}{r["price_usd"]:,} USD</dd></div></dl><p>Пример подбора. Условия поставки и состав цены уточняются; мощность по документам и льготный утильсбор не подтверждены.</p><a class="button button-primary" href="{url}">Подобрать аналог</a></div></article>')
p=Path('china-order.html');page=p.read_text()
assert page.count('class="cn-example"')==199
page=page.replace('199 примеров','210 примеров')
page=re.sub(r'(· \d{2,3} / )199</div>',r'\g<1>210</div>',page)
needle='</div><p><a href="/china-util-models.html">'
assert page.count(needle)==1
page=page.replace(needle,''.join(cards)+needle)
# Existing price terms and supplier starting prices must remain separately labelled.

assert page.count('class="cn-example"')==210
p.write_text(page)
Path('research/owner-approved-china-supplier-160hp11-2026-11-20.json').write_text(json.dumps({'owner_approval':'2026-11-20: expressly approved exact 11-card power-listed preview for publication','third_party_license_verified':False,'auction_lots':False,'source_run_ids':[44699371077,44693561445],'source_artifact_ids':[14611574333,14609981198],'records':receipt},ensure_ascii=False,indent=2)+'\n')
p=Path('china.html');s=p.read_text();assert '199 автомобилей с фотографиями' in s;p.write_text(s.replace('199 автомобилей с фотографиями','210 автомобилей с фотографиями'))
for filename in ('AGENTS.md','docs/AUCTION_ONLY_GALLERY.md'):
    p=Path(filename);p.write_text(p.read_text().rstrip()+'\n\nOwner instruction 2026-11-20: exact 11 additional power-listed supplier examples approved for china-order.html. Only the fixed seventh batch digests are allowed alongside previous 199. Supplier-listed <=160 PS is not document-verified power or a reduced-fee guarantee. Starting prices are NOT FOB. Auction safeguards unchanged; no license asserted.\n')
verify()
print('210 approved supplier photos verified; 11 new power-listed examples appended.')
