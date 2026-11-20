import hashlib, html, json, re, shutil, sys
from pathlib import Path
from urllib.parse import quote
from verify_china_order_release import EXTRA_HASHES, EXTRA_PREFIX, verify

archive=Path(sys.argv[1])
by={r['id']:r for r in json.loads((archive/'manifest.json').read_text())['records']}
old=json.loads(Path('research/owner-approved-china-supplier-49-2026-11-20.json').read_text())['records']
assert len(old)==49 and len(EXTRA_HASHES)==30
seen_urls={r['photo_url'] for r in old}
seen_hashes={r['photo_sha256'] for r in old}
seen_models={r['title'][5:].casefold() for r in old}
media=Path(EXTRA_PREFIX);media.mkdir(parents=True,exist_ok=True)
groups={'china':'Китайские марки','japan':'Японские марки','usa':'Американские марки','europe':'Европейские марки'}
brands={'Toyota':'japan','Honda':'japan','Infiniti':'japan','Chevrolet':'usa','Lincoln':'usa','Jaguar':'europe','Chery':'china','TANK':'china','Changan':'china','Geely':'china','Baojun':'china','BAIC':'china','Hongqi':'china','Haval':'china'}
e=html.escape;cards=[];receipt=[]
for num,(ident,digest) in enumerate(EXTRA_HASHES.items(),50):
    r=by[ident]
    model=r['title'][5:]
    assert re.fullmatch(r'20\d\d .+',r['title']) and model.casefold() not in seen_models
    assert r['photo_url'] not in seen_urls and digest not in seen_hashes
    assert isinstance(r['mileage_km'],int) and r['mileage_km']>=0 and r['fob_usd']>0
    src=archive/(ident+'.jpg')
    assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
    img=media/(ident+'.jpg');shutil.copyfile(src,img)
    origin=brands[model.split()[0]]
    seen_urls.add(r['photo_url']);seen_hashes.add(digest);seen_models.add(model.casefold())
    name=model+' '+r['title'][:4]
    receipt.append(dict(r,artifact_record_id=ident,photo_sha256=digest,photo_path='/'+img.as_posix(),brand_group=origin,publication_approved=True,rights_confirmed=False,documented_power_kw=None,inspection_report=None,status='supplier_reference_only'))
    url='/podbor.html?similar='+quote(name+' · КИТАЙ')
    cards.append(f'<article class="cn-example" data-origin="{origin}" data-search="{e(name+" "+r["engine"],quote=True)}"><div class="cn-overline">{groups[origin]} · {num:02d} / 79</div><img src="/{img.as_posix()}" alt="{e(name,quote=True)}" loading="lazy" decoding="async" width="1000" height="750"><div class="cn-body"><h2>{e(name)}</h2><dl><div><dt>Двигатель</dt><dd>{e(r["engine"])}</dd></div><div><dt>Пробег по данным поставщика</dt><dd>{r["mileage_km"]:,} км</dd></div><div><dt>Цена FOB на 20.11.2026</dt><dd>{r["fob_usd"]:,} USD</dd></div></dl><p>Пример подбора. Наличие, мощность по документам, диагностику и итоговую цену уточняем перед заказом.</p><a class="button button-primary" href="{url}">Подобрать аналог</a></div></article>')
p=Path('china-order.html');page=p.read_text()
assert page.count('class="cn-example"')==49
page=page.replace('49 примеров','79 примеров')
page=re.sub(r'(· \d{2} / )49</div>',r'\g<1>79</div>',page)
needle='</div><p><a href="/china-util-models.html">'
assert page.count(needle)==1
page=page.replace(needle,''.join(cards)+needle)
page=page.replace('<option value="europe">Европейские</option>','<option value="europe">Европейские</option><option value="usa">Американские</option>')
assert page.count('class="cn-example"')==79
p.write_text(page)
Path('research/owner-approved-china-supplier-30-2026-11-20.json').write_text(json.dumps({'owner_approval':'2026-11-20: expressly approved the separate 30-card preview for publication','third_party_license_verified':False,'auction_lots':False,'source_run_id':44678925244,'source_artifact_id':14603297576,'records':receipt},ensure_ascii=False,indent=2)+'\n')
p=Path('china.html');s=p.read_text();assert '49 автомобилей с фотографиями' in s;p.write_text(s.replace('49 автомобилей с фотографиями','79 автомобилей с фотографиями'))
for filename in ('AGENTS.md','docs/AUCTION_ONLY_GALLERY.md'):
    p=Path(filename);p.write_text(p.read_text().rstrip()+'\n\nOwner instruction 2026-11-20: the exact separate preview of 30 additional Chinese-market supplier examples explicitly approved for china-order.html. These are not auction listings or verified reduced-fee cars. No third-party license is asserted. Only the 30 fixed digests in verify_china_order_release.py are newly allowed, alongside the previous 49; auction safeguards unchanged. The separate five-card preview is not included in this release.\n')
verify()
print('79 approved supplier photos verified; 30 new distinct model-family references appended.')
