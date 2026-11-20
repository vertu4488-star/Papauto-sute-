import concurrent.futures, hashlib, html, io, json, re
from pathlib import Path
from urllib.parse import quote, urljoin
import requests
from bs4 import BeautifulSoup
from PIL import Image
from verify_china_order_release import verify

P=Path
assert len(verify())==220
manifest=P('research/goldenlane-next9-review-2026-11-20.json')
rows=json.loads(manifest.read_text())['records']
assert len(rows)==9 and len({x['stock_id'] for x in rows})==9
old=[]
for batch in ('49','30','third30','fourth30','fifth30','160hp30','160hp11','160hp10'):
    old+=json.loads(P(f'research/owner-approved-china-supplier-{batch}-2026-11-20.json').read_text())['records']
assert len(old)==220
urls={r['photo_url'] for r in old}; hashes={r['photo_sha256'] for r in old}
sources={r.get('source') for r in old}
headers={'User-Agent':'Mozilla/5.0'}
def get(url):
    x=requests.get(url,headers=headers,timeout=25); x.raise_for_status()
    assert x.url.startswith('https://goldenlaneauto.com/'),x.url
    return x
def prepare(r):
    assert r['source'].startswith('https://goldenlaneauto.com/used-cars/') and r['source'].endswith('-'+r['stock_id']+'/')
    assert r['photo_url'].startswith('https://goldenlaneauto.com/assets/img/cars/sc/')
    assert r['source'] not in sources and r['photo_url'] not in urls
    assert 0<r['power_hp_listed']<=160 and 0<r['power_kw_listed']<=117.68 and float(r['engine'][:3])<=2
    page=get(r['source'])
    soup=BeautifulSoup(page.text,'html.parser')
    links={urljoin(r['source'],im.get(k,'')) for im in soup.find_all('img') for k in ('src','data-src') if im.get(k)}
    assert r['photo_url'] in links, ('photo is not on exact listing',r['stock_id'])
    t=soup.get_text(' ',strip=True)
    mil=re.search(r'Mileage\s+([\d,]+)\s*km',t,re.I)
    kw=re.search(r'Max power\s+([\d.]+)\s*kW',t,re.I)
    pr=re.search(r'From\s*¥\s*([\d,]+)\s*CNY',t,re.I)
    assert mil and int(mil[1].replace(',',''))==r['mileage_km'], ('mileage changed',r['stock_id'])
    assert kw and abs(float(kw[1])-r['power_kw_listed'])<1, ('power changed',r['stock_id'])
    assert pr and int(pr[1].replace(',',''))==r['price_cny'], ('price changed',r['stock_id'])
    raw=get(r['photo_url']).content
    assert 2048<len(raw)<15000000
    im=Image.open(io.BytesIO(raw)); im.load()
    assert min(im.size)>=300
    im.thumbnail((1200,900))
    buf=io.BytesIO();im.convert('RGB').save(buf,format='JPEG',quality=92)
    return r,buf.getvalue(),hashlib.sha256(raw).hexdigest()
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as p:
    downloaded=list(p.map(prepare,rows))
prefix='assets/china-order/owner-20261120-goldenlane9/'
P(prefix).mkdir(parents=True,exist_ok=False)
groups={'Nissan':('japan','Японские марки'),'Honda':('japan','Японские марки'),'Volkswagen':('europe','Европейские марки'),'Kia':('korea','Корейские марки'),'Hyundai':('korea','Корейские марки')}
cards=[];receipt=[];new={}
for i,(r,b,rawhash) in enumerate(downloaded,221):
    digest=hashlib.sha256(b).hexdigest()
    assert digest not in hashes and r['photo_url'] not in urls
    hashes.add(digest);urls.add(r['photo_url'])
    ident=str(i-220).zfill(3);new[ident]=digest
    path=prefix+ident+'.jpg';P(path).write_bytes(b)
    origin,label=groups[r['title'].split()[0]]
    year=r['manufacture_date'][:4]
    name=r['title']+' · '+year
    hp=r['power_hp_listed']
    e=html.escape
    link='/podbor.html?similar='+quote(name+' · КИТАЙ')
    cards.append(f'<article class="cn-example" data-origin="{origin}" data-power="{hp}" data-search="{e(name+" "+r["engine"],quote=True)}"><div class="cn-overline">{label} · {i} / 229</div><img src="/{path}" alt="{e(name,quote=True)}" loading="lazy" decoding="async" width="1000" height="750"><div class="cn-body"><h2>{e(name)}</h2><dl><div><dt>Двигатель</dt><dd>{e(r["engine"])}</dd></div><div><dt>Мощность по объявлению</dt><dd>{hp} л.с.</dd></div><div><dt>Пробег по данным поставщика</dt><dd>{r["mileage_km"]:,} км</dd></div><div><dt>Начальная цена поставщика (условия уточняются)</dt><dd>от {r["price_cny"]:,} CNY</dd></div></dl><p>Пример подбора. Условия поставки и состав цены уточняются; мощность по документам и льготный утильсбор не подтверждены.</p><a class="button button-primary" href="{link}">Подобрать аналог</a></div></article>')
    receipt.append(dict(r,year=int(year),power_ps_listed=hp,photo_path='/'+path,photo_sha256=digest,source_photo_sha256=rawhash,brand_group=origin,publication_approved=True,rights_confirmed=False,status='supplier_reference_only'))
v=P('scripts/verify_china_order_release.py');s=v.read_text()
assert s.count('def verify(root=ROOT):')==1
s=s.replace('def verify(root=ROOT):', 'NINTH_PREFIX = '+repr(prefix)+'\nNINTH_HASHES = '+repr(new)+'\n\ndef verify(root=ROOT):')
needle=' | {EIGHTH_PREFIX + ident + ".jpg" for ident in EIGHTH_HASHES}'
assert s.count(needle)==1
s=s.replace(needle,needle+' | {NINTH_PREFIX + ident + ".jpg" for ident in NINTH_HASHES}')
needle='    html = (root/PAGE).read_text(encoding="utf-8")'
assert s.count(needle)==1
s=s.replace(needle,'    for ident, digest in NINTH_HASHES.items():\n        p = root / NINTH_PREFIX / (ident + ".jpg")\n        b = p.read_bytes()\n        if p.is_symlink() or len(b)<500 or not b.startswith(b"\\xff\\xd8\\xff") or hashlib.sha256(b).hexdigest()!=digest:\n            raise RuntimeError("CHINA_ORDER: approved nine photo mismatch " + ident)\n'+needle)
needle=' + ["/"+EIGHTH_PREFIX+i+".jpg" for i in EIGHTH_HASHES]'
assert s.count(needle)==1
s=s.replace(needle,needle+' + ["/"+NINTH_PREFIX+i+".jpg" for i in NINTH_HASHES]')
v.write_text(s)
p=P('china-order.html');page=p.read_text()
assert page.count('class="cn-example"')==220
page=page.replace('220 примеров','229 примеров')
page=re.sub(r'(· \d{2,3} / )220</div>',r'\g<1>229</div>',page)
needle='</div><p><a href="/china-util-models.html">'
assert page.count(needle)==1
page=page.replace(needle,''.join(cards)+needle)
assert page.count('class="cn-example"')==229
p.write_text(page)
p=P('china.html');s=p.read_text();assert '220 автомобилей с фотографиями' in s;p.write_text(s.replace('220 автомобилей с фотографиями','229 автомобилей с фотографиями'))
P('research/owner-approved-china-supplier-goldenlane9-2026-11-20.json').write_text(json.dumps({'owner_approval':'2026-11-20: user expressly approved nine exact source-linked review cards for publication','third_party_license_verified':False,'auction_lots':False,'records':receipt},ensure_ascii=False,indent=2)+'\n')
for f in ('AGENTS.md','docs/AUCTION_ONLY_GALLERY.md'):
    p=P(f);p.write_text(p.read_text().rstrip()+'\n\nOwner instruction 2026-11-20: exact nine GoldenLane source-linked supplier examples approved for china-order.html. Only fixed ninth-batch digests permitted after validation; no license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.\n')
p=P('research/CHINA_SUPPLIER_SOURCE_REGISTER.md');p.write_text(p.read_text().rstrip()+'\n\nNinth approved batch: research/owner-approved-china-supplier-goldenlane9-2026-11-20.json; 9 GoldenLane source records (19 total GoldenLane, 229 overall), exact local file and original photo SHA-256 retained. Public years use manufacture year when model year differs.\n')
print('Nine exact source images downloaded and frozen; 229 cards assembled.')
