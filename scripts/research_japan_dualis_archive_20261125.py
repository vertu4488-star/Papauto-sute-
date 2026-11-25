import requests,bs4,re,json,hashlib,io,concurrent.futures
from pathlib import Path
from urllib.parse import urljoin,urlparse
from PIL import Image,ImageDraw,ImageFont
from collections import Counter
BASE='https://atp-auto.ru'
ROOT=Path('.')
out=Path('japan-dualis-archive-review');out.mkdir(exist_ok=True)
old=[]
for path in [Path('data/gallery-lots.json'),Path('data/approved-auction-lots.json'),Path('research/owner-selected-japan-lots-2026-11-14.json'),*Path('research').glob('owner-approved-*archive*.json'),*Path('research').glob('owner-approved-japan-*.json')]:
 if not path.is_file():continue
 data=json.loads(path.read_text())
 if isinstance(data,dict):old.extend(x for x in data.get('lots',[]) if x.get('country',x.get('market','japan'))=='japan')

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
models=["nissan/dualis"]
PRIORITY_GAPS={("Toyota","Noah",2018),("Toyota","C-HR",2018),("Honda","Freed",2019),("Toyota","Tank",2016),("Nissan","X-Trail",2018),("Nissan","NV200",2017),("Mazda","CX-5",2014),("Subaru","Levorg",2021),("Toyota","Succeed",2019),("Mazda","CX-8",2017),("Mazda","CX-8",2019),("Toyota","Camry",2015)}
seen_model_year={(str(x.get('make') or '').lower()+' '+str(x.get('model') or '').lower(),int(x.get('year') or 0)) for x in old}
for x in old:
 if not x.get('make'): seen_model_year.add((str(x.get('model') or '').lower(),int(x.get('year') or 0)))

def discover(args):
 m,p=args
 try:
  soup=bs4.BeautifulSoup(get(BASE+'/avto-iz-yaponii/'+m+'/?PAGE='+str(p)).text,'html.parser')
  return list(dict.fromkeys(urljoin(BASE,a['href']).split('?')[0] for a in soup.select('a[href]') if re.search(r'/avto-iz-yaponii/[^/]+/[^/]+/[A-Za-z0-9]{8,}/?$',a['href'])))
 except Exception:return []
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool: related=list(pool.map(discover,[(m,p) for p in [1,2,3,4,5] for m in models]))
direct=["https://atp-auto.ru/avto-iz-yaponii/toyota/bb/5658c0T9bMFa9s/","https://atp-auto.ru/avto-iz-yaponii/nissan/juke/5BtgotRybOE52Tx/","https://atp-auto.ru/avto-iz-yaponii/nissan/juke/etTBK5MrlTgyQ/","https://atp-auto.ru/avto-iz-yaponii/nissan/juke/2oYX5qrlbP91tY/"]
urls=list(dict.fromkeys(u for u in direct+[v for group in related for v in group] if u.rstrip('/') not in oldurls and any(urlparse(u).path.startswith('/avto-iz-yaponii/'+m+'/') for m in models)))
# Round-robin by model, at most 12 detail pages each.
groups={m:[u for u in urls if urlparse(u).path.startswith('/avto-iz-yaponii/'+m+'/')][:12] for m in models}
urls=[groups[m][i] for i in range(12) for m in models if i<len(groups[m])]
print('new detail URLs',len(urls),flush=True)
def detail(u):
 try:
  soup=bs4.BeautifulSoup(get(u).text,'html.parser')
  h=soup.find('h1').get_text(' ',strip=True)
  ym=re.search(r'\b(20\d\d)\b',h)
  if not ym:
   print('HOLD missing title year',u,repr(h)[:120]);return None
  year=int(ym.group(1))
  if not 2000<=year<=2026:return None
  lines=list(soup.stripped_strings)
  def field(k):
   for i,t in enumerate(lines[:-1]):
    if t.strip().rstrip(':')==k:return lines[i+1].strip()
   return ''
  def num(v):return int(re.sub(r'\D','',v) or 0)
  hm=re.search(r'\d+(?:[.,]\d+)?',field('Мощность'));hp=int(float(hm.group().replace(',','.'))) if hm else None;cc=num(field('Объем'));km=num(field('Пробег'))
  grade=field('Оценка');lot=field('Номер лота');auction=field('Аукцион');date=field('Дата аукциона');price=field('Цена продажи в Японии')
  if not ((hp is None or 0<hp<=160) and 1900<cc<=2000 and km>0 and re.fullmatch(r'[3456](?:\.[05])?',grade) and float(grade)>=3.5 and re.fullmatch(r'\d{4}-\d{2}-\d{2}',date) and lot.isdigit() and auction and num(price)>0 and field('Статус').lower()=='sold'):return None
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
  make,model=re.sub(r' 20\d\d года$','',h).split(' ',1)
  if not any(norm(make+'/'+model)==norm(m) for m in models):return None
  media=[]; hashes=[]; visuals=[]
  for src in [photos[0],photos[1] if len(photos)>1 else None,sheets[0]]:
   if src is None:continue
   b=get(src).content;im=Image.open(io.BytesIO(b)).convert('RGB')
   if min(im.size)<180:return None
   sha=hashlib.sha256(b).hexdigest()
   if sha in oldhash or sha in hashes:return None
   visuals.append(dhash(im));hashes.append(sha);media.append((src,b,im))
  if any((visuals[0]^p).bit_count()<=2 for p in oldvisual):return None
  return dict(source=u,title=h,year=year,is_exact_drom_gap=(make,model,year) in PRIORITY_GAPS,auction=auction,lot=lot,date=date,grade=grade,km=km,hp=hp,cc=cc,body=field('Кузов'),trim=field('Комплектация'),price_jpy=num(price),media_urls=[x[0] for x in media],raw_sha256=hashes),media,visuals
 except Exception as e:print('skip',u,str(e)[:100]);return None
seen=set(oldkeys);hashes=set(oldhash);visuals=[]; rows=[];model_limits=Counter();year_limits=Counter()
# Bounded first pass, balanced across models.
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
 for result in pool.map(detail,urls[:650]):
  if not result:continue
  r,imgs,v=result;k=(norm(r['auction']),r['date'],r['lot'].lstrip('0'))
  if k in seen or hashes.intersection(r['raw_sha256']) or any((v[0]^p).bit_count()<=2 for p in visuals):continue
  slug=re.sub(r' 20\d\d года$','',r['title']);modelyear=(slug.lower(),r['year'])
  if model_limits[slug]>=3 or year_limits[modelyear]>=2:continue
  seen.add(k);hashes.update(r['raw_sha256']);visuals.append(v[0]);model_limits[slug]+=1;year_limits[modelyear]+=1
  n=len(rows)+1;r['index']=n;files=[]
  for j,(u,b,im) in enumerate(imgs):
   name=f'{n:03d}-{j}.jpg';im.save(out/name,quality=95);files.append(name)
  r['files']=files;r.update(publish_state='HOLD',rights_confirmed=False,visual_review_confirmed=False,full_sheet_match_confirmed=False,owner_batch_approved=False,archival_only=True,eligible_for_direct_export_to_russia=False);rows.append(r)
  if len(rows)>=3:break
print('JAPAN_MODEL_GAP_CANDIDATE_SETS',len(rows),flush=True)
print('JAPAN_MODEL_GAP_COUNTS',dict(model_limits),flush=True)
(out/'manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
for a in range(0,len(rows),10):
 rr=rows[a:a+10]; sheet=Image.new('RGB',(1200,200*len(rr)), '#f7f3eb');d=ImageDraw.Draw(sheet)
 for i,r in enumerate(rr):
  y=i*200;d.text((10,y+3),f"{r['index']:03d} {r['title']} | {r['auction']} | {r['lot']} | {r['grade']}",font=font,fill='#202020')
  for j,name in enumerate(r['files']):
   im=Image.open(out/name);im.thumbnail((390,170));sheet.paste(im,(j*400+(400-im.width)//2,y+25))
 sheet.save(out/f'contact-{a//10:02d}.jpg',quality=90)
