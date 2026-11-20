import hashlib, html, json, re, shutil, sys
from pathlib import Path
from urllib.parse import quote
from verify_china_order_release import EIGHTH_HASHES, EIGHTH_PREFIX, verify

archive=Path(sys.argv[1])
by={r['id']:r for r in json.loads((archive/'manifest.json').read_text())['records']}
old=[]
for batch in ('49','30','third30','fourth30','fifth30','160hp30','160hp11'):
    old+=json.loads(Path(f'research/owner-approved-china-supplier-{batch}-2026-11-20.json').read_text())['records']
assert len(old)==210 and len(EIGHTH_HASHES)==10
seen_urls={r['photo_url'] for r in old}
seen_hashes={r['photo_sha256'] for r in old}
media=Path(EIGHTH_PREFIX);media.mkdir(parents=True,exist_ok=True)
groups={'china':'Китайские марки','japan':'Японские марки','usa':'Американские марки','europe':'Европейские марки','korea':'Корейские марки'}
brands={'mazda':'japan','toyota':'japan','nissan':'japan','honda':'japan','mitsubishi':'japan','suzuki':'japan','subaru':'japan','kia':'korea','hyundai':'korea','volkswagen':'europe','vw':'europe','jetta':'europe','skoda':'europe','škoda':'europe','audi':'europe','bmw':'europe','mercedes':'europe','mercedes-benz':'europe','mini':'europe','volvo':'europe','peugeot':'europe','citroen':'europe','mg':'china','geely':'china','chery':'china','haval':'china','changan':'china','gac':'china','jetour':'china','dongfeng':'china','roewe':'china','wuling':'china','byd':'china','chevrolet':'usa','ford':'usa','buick':'usa'}
review=json.loads(Path('research/china-order-160hp-next10-review-2026-11-20.json').read_text())['records']
selected={r['key']:r for r in review}
archives={44703549078:Path(sys.argv[1]),44703760612:Path(sys.argv[2]),44703941117:Path(sys.argv[3])}
e=html.escape;cards=[];receipt=[]
for num,(ident,digest) in enumerate(EIGHTH_HASHES.items(),211):
    ref=selected[ident]
    source_run=ref['artifact_run_id']
    source_archive=archives[source_run]
    source_id=ref['id']
    r=dict({x['id']:x for x in json.loads((source_archive/'manifest.json').read_text())['records']}[source_id])
    hp=r['power_ps_listed']
    assert float(r['power_kw_listed'])<=117.68
    assert hp==ref['power_ps_listed'] and 0<hp<=160
    assert float(re.search(r'\d\.\d',r['engine']).group())<=2
    assert r['photo_url'] not in seen_urls and digest not in seen_hashes
    assert isinstance(r['mileage_km'],int) and r['mileage_km']>=0 and r['price_cny']>0
    src=source_archive/(source_id+'.jpg')
    assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
    img=media/(ident+'.jpg');shutil.copyfile(src,img)
    model=html.unescape(r['title']).strip()
    origin=brands[model.split()[0].casefold()]
    seen_urls.add(r['photo_url']);seen_hashes.add(digest)
    name=model+' · '+str(r['year'])
    price_label='Начальная цена поставщика (условия уточняются)'
    price_prefix='от '
    r['price_type']='supplier starting route price CNY, not FOB'
    receipt.append(dict(r,artifact_record_id=source_id,photo_sha256=digest,source_run_id=source_run,photo_path='/'+img.as_posix(),brand_group=origin,publication_approved=True,rights_confirmed=False,documented_power_kw=None,inspection_report=None,status='supplier_reference_only'))
    url='/podbor.html?similar='+quote(name+' · КИТАЙ')
    cards.append(f'<article class="cn-example" data-origin="{origin}" data-power="{hp}" data-search="{e(name+" "+r["engine"],quote=True)}"><div class="cn-overline">{groups[origin]} · {num} / 220</div><img src="/{img.as_posix()}" alt="{e(name,quote=True)}" loading="lazy" decoding="async" width="1000" height="750"><div class="cn-body"><h2>{e(name)}</h2><dl><div><dt>Двигатель</dt><dd>{e(r["engine"])}</dd></div><div><dt>Мощность по объявлению</dt><dd>{hp} л.с.</dd></div><div><dt>Пробег по данным поставщика</dt><dd>{r["mileage_km"]:,} км</dd></div><div><dt>{price_label}</dt><dd>{price_prefix}{r["price_cny"]:,} CNY</dd></div></dl><p>Пример подбора. Условия поставки и состав цены уточняются; мощность по документам и льготный утильсбор не подтверждены.</p><a class="button button-primary" href="{url}">Подобрать аналог</a></div></article>')
p=Path('china-order.html');page=p.read_text()
assert page.count('class="cn-example"')==210
page=page.replace('210 примеров','220 примеров')
page=re.sub(r'(· \d{2,3} / )210</div>',r'\g<1>220</div>',page)
needle='</div><p><a href="/china-util-models.html">'
assert page.count(needle)==1
page=page.replace(needle,''.join(cards)+needle)
# Existing price terms and supplier starting prices must remain separately labelled.

assert page.count('class="cn-example"')==220
p.write_text(page)
Path('research/owner-approved-china-supplier-160hp10-2026-11-20.json').write_text(json.dumps({'owner_approval':'2026-11-20: expressly approved exact 10-card power-listed preview for publication','third_party_license_verified':False,'auction_lots':False,'source_run_ids':[44703549078,44703760612,44703941117],'source_artifact_ids':[14613827343,14614495422,14613198955],'records':receipt},ensure_ascii=False,indent=2)+'\n')
p=Path('china.html');s=p.read_text();assert '210 автомобилей с фотографиями' in s;p.write_text(s.replace('210 автомобилей с фотографиями','220 автомобилей с фотографиями'))
for filename in ('AGENTS.md','docs/AUCTION_ONLY_GALLERY.md'):
    p=Path(filename);p.write_text(p.read_text().rstrip()+'\n\nOwner instruction 2026-11-20: exact 10 additional power-listed supplier examples approved for china-order.html. Only the fixed eighth batch digests are allowed alongside previous 210. Supplier-listed <=160 PS is not document-verified power or a reduced-fee guarantee. Starting prices are NOT FOB. Auction safeguards unchanged; no license asserted.\n')
verify()
print('220 approved supplier photos verified; 10 new power-listed examples appended.')
