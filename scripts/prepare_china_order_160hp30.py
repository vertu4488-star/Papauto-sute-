import hashlib, html, json, re, shutil, sys
from pathlib import Path
from urllib.parse import quote
from verify_china_order_release import SIXTH_HASHES, SIXTH_PREFIX, verify

archive=Path(sys.argv[1])
by={r['id']:r for r in json.loads((archive/'manifest.json').read_text())['records']}
old=[]
for batch in ('49','30','third30','fourth30','fifth30'):
    old+=json.loads(Path(f'research/owner-approved-china-supplier-{batch}-2026-11-20.json').read_text())['records']
assert len(old)==169 and len(SIXTH_HASHES)==30
seen_urls={r['photo_url'] for r in old}
seen_hashes={r['photo_sha256'] for r in old}
media=Path(SIXTH_PREFIX);media.mkdir(parents=True,exist_ok=True)
groups={'china':'Китайские марки','japan':'Японские марки','usa':'Американские марки','europe':'Европейские марки','korea':'Корейские марки'}
brands={'mazda':'japan','toyota':'japan','nissan':'japan','honda':'japan','mitsubishi':'japan','suzuki':'japan','subaru':'japan','kia':'korea','hyundai':'korea','volkswagen':'europe','vw':'europe','jetta':'europe','skoda':'europe','škoda':'europe','audi':'europe','bmw':'europe','mercedes':'europe','mercedes-benz':'europe','mini':'europe','volvo':'europe','peugeot':'europe','citroen':'europe','mg':'china','geely':'china','chery':'china','haval':'china','changan':'china','gac':'china','jetour':'china','dongfeng':'china','roewe':'china','wuling':'china','byd':'china','chevrolet':'usa','ford':'usa','buick':'usa'}
powers={'001':158,'002':115,'009':156,'010':110,'012':150,'021':150,'028':121,'041':150,'043':150,'045':149,'047':149,'048':110,'054':108,'061':150,'064':120,'065':149,'076':150,'005':155,'011':151,'027':115,'044':149,'046':110,'057':150,'058':158,'059':150,'066':150,'067':124,'072':150,'062':150,'060':150}
e=html.escape;cards=[];receipt=[]
for num,(ident,digest) in enumerate(SIXTH_HASHES.items(),170):
    r=dict(by[ident]); hp=r['power_ps_listed']
    assert hp==powers[ident] and 0<hp<=160
    assert float(re.search(r'\d\.\d',r['engine']).group())<=2
    assert r['photo_url'] not in seen_urls and digest not in seen_hashes
    assert isinstance(r['mileage_km'],int) and r['mileage_km']>=0 and r['price_usd']>0
    src=archive/(ident+'.jpg')
    assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
    img=media/(ident+'.jpg');shutil.copyfile(src,img)
    model=html.unescape(r['title']).strip()
    origin=brands[model.split()[0].casefold()]
    seen_urls.add(r['photo_url']);seen_hashes.add(digest)
    name=model+' · '+str(r['year'])
    receipt.append(dict(r,artifact_record_id=ident,photo_sha256=digest,source_run_id=44699371077,photo_path='/'+img.as_posix(),brand_group=origin,publication_approved=True,rights_confirmed=False,documented_power_kw=None,inspection_report=None,status='supplier_reference_only'))
    url='/podbor.html?similar='+quote(name+' · КИТАЙ')
    cards.append(f'<article class="cn-example" data-origin="{origin}" data-power="{hp}" data-search="{e(name+" "+r["engine"],quote=True)}"><div class="cn-overline">{groups[origin]} · {num} / 199</div><img src="/{img.as_posix()}" alt="{e(name,quote=True)}" loading="lazy" decoding="async" width="1000" height="750"><div class="cn-body"><h2>{e(name)}</h2><dl><div><dt>Двигатель</dt><dd>{e(r["engine"])}</dd></div><div><dt>Мощность по объявлению</dt><dd>{hp} л.с.</dd></div><div><dt>Пробег по данным поставщика</dt><dd>{r["mileage_km"]:,} км</dd></div><div><dt>Цена поставщика от 20.11.2026</dt><dd>от {r["price_usd"]:,} USD</dd></div></dl><p>Пример подбора. Условия поставки и состав цены уточняются; мощность по документам и льготный утильсбор не подтверждены.</p><a class="button button-primary" href="{url}">Подобрать аналог</a></div></article>')
p=Path('china-order.html');page=p.read_text()
assert page.count('class="cn-example"')==169
page=page.replace('169 примеров','199 примеров')
page=re.sub(r'(· \d{2,3} / )169</div>',r'\g<1>199</div>',page)
needle='</div><p><a href="/china-util-models.html">'
assert page.count(needle)==1
page=page.replace(needle,''.join(cards)+needle)
# Existing price terms and supplier starting prices must remain separately labelled.
page=page.replace('Цена FOB не включает таможню, утильсбор и доставку в Россию.', 'Цена FOB не включает таможню, утильсбор и доставку в Россию. Для новых карточек с заявленной мощностью до 160 л.с. указаны начальные цены поставщика; условия поставки и состав цены уточняются.')
assert page.count('class="cn-example"')==199
p.write_text(page)
Path('research/owner-approved-china-supplier-160hp30-2026-11-20.json').write_text(json.dumps({'owner_approval':'2026-11-20: expressly approved exact 30-card power-listed preview for publication','third_party_license_verified':False,'auction_lots':False,'source_run_id':44699371077,'source_artifact_id':14611574333,'records':receipt},ensure_ascii=False,indent=2)+'\n')
p=Path('china.html');s=p.read_text();assert '169 автомобилей с фотографиями' in s;p.write_text(s.replace('169 автомобилей с фотографиями','199 автомобилей с фотографиями'))
for filename in ('AGENTS.md','docs/AUCTION_ONLY_GALLERY.md'):
    p=Path(filename);p.write_text(p.read_text().rstrip()+'\n\nOwner instruction 2026-11-20: exact 30 additional power-listed supplier examples approved for china-order.html. Only the fixed sixth batch digests are allowed alongside previous 169. Supplier-listed <=160 PS is not document-verified power or a reduced-fee guarantee. Starting prices are NOT FOB. Auction safeguards unchanged; no license asserted.\n')
verify()
print('199 approved supplier photos verified; 30 new power-listed examples appended.')
