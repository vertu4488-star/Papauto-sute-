import hashlib, html, json, re, shutil, sys
from pathlib import Path
from urllib.parse import quote
from verify_china_order_release import FIFTH_HASHES, FIFTH_PREFIX, verify

archive=Path(sys.argv[1])
by={r['id']:r for r in json.loads((archive/'manifest.json').read_text())['records']}
old=json.loads(Path('research/owner-approved-china-supplier-49-2026-11-20.json').read_text())['records']
old+=json.loads(Path('research/owner-approved-china-supplier-30-2026-11-20.json').read_text())['records']
old+=json.loads(Path('research/owner-approved-china-supplier-third30-2026-11-20.json').read_text())['records']
old+=json.loads(Path('research/owner-approved-china-supplier-fourth30-2026-11-20.json').read_text())['records']
assert len(old)==139 and len(FIFTH_HASHES)==30
seen_urls={r['photo_url'] for r in old}
seen_hashes={r['photo_sha256'] for r in old}
seen_models={r['title'][5:].casefold() for r in old}
media=Path(FIFTH_PREFIX);media.mkdir(parents=True,exist_ok=True)
groups={'china':'Китайские марки','japan':'Японские марки','usa':'Американские марки','europe':'Европейские марки','korea':'Корейские марки'}
origins={'175':'china','223':'china','240':'china','244':'china','126':'china','288':'china','289':'china','179':'europe','150':'europe','168':'europe','181':'europe','207':'europe','216':'europe','221':'europe','228':'europe','232':'europe','233':'europe','235':'europe','246':'europe','247':'europe','350':'korea','133':'usa','166':'usa','172':'usa','194':'usa','219':'usa','241':'usa','290':'usa','120':'usa','002':'usa'}
e=html.escape;cards=[];receipt=[]
for num,(ident,digest) in enumerate(FIFTH_HASHES.items(),140):
    source_archive = archive if ident != '002' else Path(sys.argv[2])
    source_run = 44692952021 if ident != '002' else 44692997948
    r=by[ident] if ident != '002' else {r['id']:r for r in json.loads((source_archive/'manifest.json').read_text())['records']}[ident]
    r=dict(r)
    model=html.unescape(r['title'][5:])
    assert re.fullmatch(r'20\d\d .+',r['title']) and model.casefold() not in seen_models
    assert r['photo_url'] not in seen_urls and digest not in seen_hashes
    assert isinstance(r['mileage_km'],int) and r['mileage_km']>=0 and r['fob_usd']>0
    src=source_archive/(ident+'.jpg')
    assert hashlib.sha256(src.read_bytes()).hexdigest()==digest
    img=media/(ident+'.jpg');shutil.copyfile(src,img)
    origin=origins[ident]
    seen_urls.add(r['photo_url']);seen_hashes.add(digest);seen_models.add(model.casefold())
    name=model+' '+r['title'][:4]
    receipt.append(dict(r,artifact_record_id=ident,photo_sha256=digest,source_run_id=source_run,photo_path='/'+img.as_posix(),brand_group=origin,publication_approved=True,rights_confirmed=False,documented_power_kw=None,inspection_report=None,status='supplier_reference_only'))
    url='/podbor.html?similar='+quote(name+' · КИТАЙ')
    cards.append(f'<article class="cn-example" data-origin="{origin}" data-search="{e(name+" "+r["engine"],quote=True)}"><div class="cn-overline">{groups[origin]} · {num:02d} / 169</div><img src="/{img.as_posix()}" alt="{e(name,quote=True)}" loading="lazy" decoding="async" width="1000" height="750"><div class="cn-body"><h2>{e(name)}</h2><dl><div><dt>Двигатель</dt><dd>{e(r["engine"])}</dd></div><div><dt>Пробег по данным поставщика</dt><dd>{r["mileage_km"]:,} км</dd></div><div><dt>Цена FOB на 20.11.2026</dt><dd>{r["fob_usd"]:,} USD</dd></div></dl><p>Пример подбора. Наличие, мощность по документам, диагностику и итоговую цену уточняем перед заказом.</p><a class="button button-primary" href="{url}">Подобрать аналог</a></div></article>')
p=Path('china-order.html');page=p.read_text()
assert page.count('class="cn-example"')==139
page=page.replace('139 примеров','169 примеров')
page=re.sub(r'(· \d{2,3} / )139</div>',r'\g<1>169</div>',page)
needle='</div><p><a href="/china-util-models.html">'
assert page.count(needle)==1
page=page.replace(needle,''.join(cards)+needle)

assert page.count('class="cn-example"')==169
p.write_text(page)
Path('research/owner-approved-china-supplier-fifth30-2026-11-20.json').write_text(json.dumps({'owner_approval':'2026-11-20: expressly approved the separate 30-card preview for publication','third_party_license_verified':False,'auction_lots':False,'source_run_ids':[44692952021,44692997948],'source_artifact_ids':[14609442433,14609900076],'records':receipt},ensure_ascii=False,indent=2)+'\n')
p=Path('china.html');s=p.read_text();assert '139 автомобилей с фотографиями' in s;p.write_text(s.replace('139 автомобилей с фотографиями','169 автомобилей с фотографиями'))
for filename in ('AGENTS.md','docs/AUCTION_ONLY_GALLERY.md'):
    p=Path(filename);p.write_text(p.read_text().rstrip()+'\n\nOwner instruction 2026-11-20: the exact separate preview of 30 additional Chinese-market supplier examples explicitly approved for china-order.html. These are not auction listings or verified reduced-fee cars. No third-party license is asserted. Only the fifth batch of 30 fixed digests in verify_china_order_release.py is newly allowed, alongside the previous 139; auction safeguards unchanged.\n')
verify()
print('169 approved supplier photos verified; 30 new distinct model-family references appended.')
