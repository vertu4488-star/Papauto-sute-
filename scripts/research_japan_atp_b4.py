import requests,bs4,re,json,hashlib,io,concurrent.futures
from pathlib import Path
from urllib.parse import urljoin,urlparse
from PIL import Image,ImageDraw,ImageFont
from collections import Counter
BASE='https://atp-auto.ru'
ROOT=Path('.')
out=Path('atp-review');out.mkdir(exist_ok=True)
old=[]
for path in ['research/owner-selected-japan-lots-2026-11-14.json','research/owner-approved-50-archive-2026-11-19.json','research/owner-approved-second-50-archive-2026-11-19.json','data/gallery-lots.json','research/owner-approved-japan-atp-30-archive-2026-11-20.json','research/owner-approved-japan-atp-second-30-archive-2026-11-20.json','research/owner-approved-japan-atp-third-30-archive-2026-11-20.json']:
 old.extend(json.loads(Path(path).read_text())['lots'])
def norm(s):return re.sub(r'[^a-z0-9]','',str(s).lower())
oldkeys={(norm(x.get('auction')),str(x.get('auction_date',''))[:10],str(x.get('lot',x.get('lot_number',''))).lstrip('0')) for x in old}
oldurls={str(x.get('source_listing','')).rstrip('/') for x in old}
oldhash={h for x in old for h in x.get('media_sha256',[])}
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
seeds=[BASE+'/avto-iz-yaponii/'+p+'/' for p in ["toyota/yaris/71cz5eMlc2trcDq","toyota/yaris/xuG9MLu7vKDqFm","toyota/yaris/36UnuMoYvaCgF2a","honda/vezel/4YkioOQ8LWydwbp","toyota/yaris/4jWkrC0pKG8tAM","toyota/yaris/376HQDjY0odqJxD","toyota/yaris/47ySqqUi3xAtpv","toyota/yaris/lJoXd82LWspFO","honda/vezel/3fZXFhTsDpRwGp","toyota/yaris/7NooFoZAS45lAA","toyota/yaris/2IV6LXN2MdeYOX","toyota/yaris/J6lnJyXTHRbl1y","toyota/yaris/36WbS8gJz8PEAMw","toyota/yaris/33p9DMHsNhDKhw","honda/vezel/4YNKw3qI4IjeUlq","toyota/yaris/30cy0xiseXYMiu","toyota/sienta/3hv3JJcsimIOzmm","toyota/sienta/IFY82ql1kPMijA","toyota/raize/2YMnY4bkLJe7vl","toyota/yaris/2FKqVWIam6jBet","toyota/raize/4jfvMvdJKPHrZV","toyota/yaris/IU22SDYfug2gu6","toyota/c-hr/8DvdAPzb61pSNv","toyota/raize/3MaDTb8kh7MjdJ","toyota/yaris/JiiktYRpZL6KN","toyota/aqua/l6mXXoak2vPDq","toyota/c-hr/3HrV7DRfaU90A","toyota/prius/5A6SVdK1LWA2tN","honda/vezel/5kGGyQMYnR6aDM","toyota/voxy/4UpS4ymQurVl0M6","toyota/voxy/56tsqBQdRXQ6Oqy","toyota/voxy/56yTyCrv4PufBIC","toyota/voxy/56t1kM8MBtxfkur","toyota/corolla-fielder/s5IDfgKCcjaQE","toyota/prius/3b8sAwsx8Q3hF9T","daihatsu/thor/579GZw5f5rv8L4v","suzuki/jimny/YKR99jQ6uiLJBh","suzuki/jimny/sEfKKxUMSyjcbd","mazda/cx-5/HtUZCdNlEJn6G","suzuki/jimny/7abxBFT5uPWaIR2","suzuki/jimny/38fKOghTrheucnL","suzuki/jimny-sierra/4Ljj6O5HSr8fA","mazda/cx-30/2MxQrHj0ING3Tx","suzuki/swift/3h3WU1LbO4SkD2l","honda/vezel/8cjzxPbdKLCUlb","honda/vezel/NPeFEnwj3dVai","honda/vezel/4nkmhXb9m3bUnv","suzuki/jimny/0WXgzG99OQ6Cn","subaru/xv/QQpxqrG53qVGip","subaru/xv/JrfzuwmlwSf7B3","suzuki/jimny/39yREzAC3LE1DOp","suzuki/hustler/AGvtRCOLoHJpH","suzuki/jimny/40JxgrZaxrU6pf","suzuki/jimny/dzHWjcg4fBX04"]]
def discover_related(u):
 try:
  soup=bs4.BeautifulSoup(get(u).text,'html.parser')
  return list(dict.fromkeys(urljoin(BASE,a['href']).split('?')[0] for a in soup.select('a[href]') if re.search(r'/avto-iz-yaponii/[^/]+/[^/]+/[A-Za-z0-9]{8,}/?$',a['href'])))
 except Exception:return []
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool: related=list(pool.map(discover_related,seeds))
urls=list(dict.fromkeys(u for u in seeds+[u for group in related for u in group] if u.rstrip('/') not in oldurls))
print('new detail URLs',len(urls),flush=True)
def detail(u):
 try:
  soup=bs4.BeautifulSoup(get(u).text,'html.parser')
  h=soup.find('h1').get_text(' ',strip=True)
  year=int(re.search(r'\b(20\d\d)\b',h).group(1))
  if not 2017<=year<=2025:return None
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
  return dict(source=u,title=h,year=year,auction=auction,lot=lot,date=date,grade=grade,km=km,hp=hp,cc=cc,body=field('Кузов'),trim=field('Комплектация'),price_jpy=num(price),media_urls=[x[0] for x in media],raw_sha256=hashes),media,visuals
 except Exception as e:print('skip',u,str(e)[:100]);return None
seen=set(oldkeys);hashes=set(oldhash);visuals=[]; rows=[]
# Bounded first pass, balanced across models.
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
 for result in pool.map(detail,urls[:500]):
  if not result:continue
  r,imgs,v=result;k=(norm(r['auction']),r['date'],r['lot'].lstrip('0'))
  if k in seen or hashes.intersection(r['raw_sha256']) or any((v[0]^p).bit_count()<=2 for p in visuals):continue
  seen.add(k);hashes.update(r['raw_sha256']);visuals.append(v[0])
  n=len(rows)+1;r['index']=n;files=[]
  for j,(u,b,im) in enumerate(imgs):
   name=f'{n:03d}-{j}.jpg';im.save(out/name,quality=95);files.append(name)
  r['files']=files;rows.append(r)
print('complete unique sets',len(rows),flush=True)
(out/'manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
for a in range(0,len(rows),10):
 rr=rows[a:a+10]; sheet=Image.new('RGB',(1200,200*len(rr)), '#f7f3eb');d=ImageDraw.Draw(sheet)
 for i,r in enumerate(rr):
  y=i*200;d.text((10,y+3),f"{r['index']:03d} {r['title']} | {r['auction']} | {r['lot']} | {r['grade']}",font=font,fill='#202020')
  for j,name in enumerate(r['files']):
   im=Image.open(out/name);im.thumbnail((390,170));sheet.paste(im,(j*400+(400-im.width)//2,y+25))
 sheet.save(out/f'contact-{a//10:02d}.jpg',quality=90)
