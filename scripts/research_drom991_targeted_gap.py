import requests,bs4,re,json,hashlib,io,concurrent.futures
from pathlib import Path
from urllib.parse import urljoin,urlparse
from PIL import Image,ImageDraw,ImageFont
from collections import Counter
BASE='https://atp-auto.ru'
ROOT=Path('.')
out=Path('drom-gap-review');out.mkdir(exist_ok=True)
old=[]
for path in ['research/owner-selected-japan-lots-2026-11-14.json','research/owner-approved-50-archive-2026-11-19.json','research/owner-approved-second-50-archive-2026-11-19.json','data/gallery-lots.json','research/owner-approved-japan-atp-30-archive-2026-11-20.json','research/owner-approved-japan-atp-second-30-archive-2026-11-20.json','research/owner-approved-japan-atp-third-30-archive-2026-11-20.json','research/owner-approved-japan-atp-fourth-30-archive-2026-11-20.json','research/owner-approved-japan-atp-fifth-30-archive-2026-11-20.json','research/owner-approved-japan-atp-sixth-30-archive-2026-11-21.json']:
 old.extend(json.loads(Path(path).read_text())['lots'])
def norm(s):return re.sub(r'[^a-z0-9]','',str(s).lower())
oldkeys={(norm(x.get('auction')),str(x.get('auction_date',''))[:10],str(x.get('lot',x.get('lot_number',''))).lstrip('0')) for x in old}
oldurls={str(x.get('source_listing','')).rstrip('/') for x in old}
oldhash={h for x in old for h in x.get('media_sha256',[])+x.get('raw_sha256',[])}
def dhash(im):
 p=list(im.convert('L').resize((9,8),Image.Resampling.LANCZOS).getdata())
 return sum(int(p[y*9+x+1]>p[y*9+x])<<(63-y*8-x) for y in range(8) for x in range(8))
oldvisual=[]
for x in old:
 for p in x.get('photos',[]):
  try:oldvisual.append(dhash(Image.open(p.lstrip('/'))))
  except:pass
def get(u):
 r=requests.get(u,timeout=18,headers={'User-Agent':'Mozilla/5.0'});r.raise_for_status();return r
models="nissan/nv200 toyota/vitz toyota/voxy mazda/cx-5 toyota/c-hr subaru/levorg honda/freed-spike toyota/allion toyota/succeed honda/freed suzuki/hustler nissan/sylphy toyota/tank toyota/noah toyota/sienta toyota/ractis mazda/cx-8 nissan/x-trail nissan/dayz".split()
TARGET_YEARS={"nissan/nv200":[2017],"toyota/vitz":[2018],"toyota/voxy":[2018],"mazda/cx-5":[2014],"toyota/c-hr":[2018],"subaru/levorg":[2021],"honda/freed-spike":[2012],"toyota/allion":[2009],"toyota/succeed":[2019],"honda/freed":[2019],"suzuki/hustler":[2014],"nissan/sylphy":[2019],"toyota/tank":[2016],"toyota/noah":[2018,2019],"toyota/sienta":[2016],"toyota/ractis":[2013],"mazda/cx-8":[2017,2019],"nissan/x-trail":[2018],"nissan/dayz":[2018]}
SEEDS=["https://atp-auto.ru/avto-iz-yaponii/honda/freed-spike/zjXFjXqAYhU9WG/","https://atp-auto.ru/avto-iz-yaponii/honda/freed-spike/7afCsbl2TeFN5k6/","https://atp-auto.ru/avto-iz-yaponii/toyota/vitz/32H0VjdIu8AliOg/","https://atp-auto.ru/avto-iz-yaponii/toyota/vitz/32dHO6D9clPjUEf/","https://atp-auto.ru/avto-iz-yaponii/toyota/voxy/7a1FlEGw7bEIR76/","https://atp-auto.ru/avto-iz-yaponii/toyota/voxy/56OiKYOs7rP32Ie/","https://atp-auto.ru/avto-iz-yaponii/toyota/voxy/646Uj6T34oKVHt/"]
for r in json.loads(Path('research/papauto-drom991-concrete-auction-lot-photo-sheet-intake-2026-11-13.json').read_text())['records']:
 if any(r['model'].lower()==key.split('/')[0]+' '+key.split('/')[1].replace('-',' ') and r['year'] in years for key,years in TARGET_YEARS.items()):SEEDS.append(r['original_source_page_url_research_only'])
def discover(args):
 m,p=args
 try:
  soup=bs4.BeautifulSoup(get(BASE+'/avto-iz-yaponii/'+m+'/?PAGE='+str(p)).text,'html.parser')
  return list(dict.fromkeys(urljoin(BASE,a['href']).split('?')[0] for a in soup.select('a[href]') if re.search(r'/avto-iz-yaponii/[^/]+/[^/]+/[A-Za-z0-9]{8,}/?$',a['href'])))
 except Exception:return []
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool: related=list(pool.map(discover,[(m,p) for p in [1,2,3,4] for m in models]))
urls=list(dict.fromkeys(u for u in SEEDS+[u for group in related for u in group] if u.rstrip('/') not in oldurls))
print('new detail URLs',len(urls),flush=True)
def detail(u):
 try:
  soup=bs4.BeautifulSoup(get(u).text,'html.parser')
  h=soup.find('h1').get_text(' ',strip=True)
  year=int(re.search(r'\b(20\d\d)\b',h).group(1))
  slug='/'.join(urlparse(u).path.strip('/').split('/')[1:3])
  if year not in TARGET_YEARS.get(slug,[]):return None
  lines=list(soup.stripped_strings)
  def field(k):
   for i,t in enumerate(lines[:-1]):
    if t.strip().rstrip(':')==k:return lines[i+1].strip()
   return ''
  def num(v):return int(re.sub(r'\D','',v) or 0)
  hp=int(float(re.search(r'\d+(?:[.,]\d+)?',field('Мощность')).group().replace(',','.')));cc=num(field('Объем'));km=num(field('Пробег'))
  grade=field('Оценка');lot=field('Номер лота');auction=field('Аукцион');date=field('Дата аукциона');price=field('Цена продажи в Японии')
  if not (0<hp<=160 and 0<cc<=2000 and km>0 and re.fullmatch(r'[3456](?:\.[05])?',grade) and float(grade)>=3.5 and re.fullmatch(r'\d{4}-\d{2}-\d{2}',date) and lot.isdigit() and auction and num(price)>0 and field('Статус').lower()=='sold'):return None
  if (norm(auction),date,lot.lstrip('0')) in oldkeys or not re.search(r'^(TAA|CAA|JU|KCAA|USS|HAA|LAA|JAA|MIRIVE|NAA|ZIP|ARAI|Honda)\b',auction,re.I):return None
  photos=[]; sheets=[]
  for im in soup.select('img[alt]'):
   alt=im.get('alt','').lower()
   if 'фото с аукциона японии' not in alt:continue
   a=im.find_parent('a',href=True)
   src=(a.get('href') if a else '') or im.get('data-src') or im.get('src')
   if not src:continue
   src=urljoin(u,src)
   if urlparse(src).hostname!='7.tru.ru':continue
   if 'аукционный лист' in alt:sheets.append(src)
   else:photos.append(src)
  photos=list(dict.fromkeys(photos));sheets=list(dict.fromkeys(sheets))
  if len(photos)<2 or len(sheets)!=1:return None
  media=[]; hashes=[]; visuals=[]
  for src in [photos[0],photos[1] if len(photos)>1 else None,sheets[0]]:
   if src is None:continue
   b=get(src).content;im=Image.open(io.BytesIO(b)).convert('RGB')
   if min(im.size)<180:return None
   sha=hashlib.sha256(b).hexdigest()
   if sha in oldhash or sha in hashes:return None
   visuals.append(dhash(im));hashes.append(sha);media.append((src,b,im))
  if any((visuals[0]^p).bit_count()<=2 for p in oldvisual):return None
  return dict(source=u,title=h,year=year,requested_gap=slug+' '+str(year),auction=auction,lot=lot,date=date,grade=grade,km=km,hp=hp,cc=cc,body=field('Кузов'),trim=field('Комплектация'),price_jpy=num(price),media_urls=[x[0] for x in media],raw_sha256=hashes),media,visuals
 except Exception as e:print('skip',u,str(e)[:100]);return None
seen=set(oldkeys);hashes=set(oldhash);visuals=[]; rows=[]
# Bounded first pass, balanced across models.
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
 for result in pool.map(detail,urls[:850]):
  if not result:continue
  r,imgs,v=result;k=(norm(r['auction']),r['date'],r['lot'].lstrip('0'))
  if k in seen or hashes.intersection(r['raw_sha256']) or any((v[0]^p).bit_count()<=2 for p in visuals):continue
  seen.add(k);hashes.update(r['raw_sha256']);visuals.append(v[0])
  n=len(rows)+1;r['index']=n;files=[]
  for j,(u,b,im) in enumerate(imgs):
   name=f'{n:03d}-{j}.jpg';im.save(out/name,quality=95);files.append(name)
  r['files']=files;rows.append(r)
print('complete distinct targeted gap sets',len(rows),flush=True)
(out/'manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
for a in range(0,len(rows),10):
 rr=rows[a:a+10]; sheet=Image.new('RGB',(1200,200*len(rr)), '#f7f3eb');d=ImageDraw.Draw(sheet)
 for i,r in enumerate(rr):
  y=i*200;d.text((10,y+3),f"{r['index']:03d} {r['title']} | {r['auction']} | {r['lot']} | {r['grade']}",font=font,fill='#202020')
  for j,name in enumerate(r['files']):
   im=Image.open(out/name);im.thumbnail((390,170));sheet.paste(im,(j*400+(400-im.width)//2,y+25))
 sheet.save(out/f'contact-{a//10:02d}.jpg',quality=90)
