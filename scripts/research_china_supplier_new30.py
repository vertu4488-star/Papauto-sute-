import requests,bs4,re,json,hashlib,io,concurrent.futures
from pathlib import Path
from urllib.parse import urljoin,urlparse
from PIL import Image,ImageDraw,ImageFont
P=Path
out=P('drom991-china-new30-review');out.mkdir(exist_ok=True)
old=[]
for p in P('research').glob('owner-approved-china-supplier-*.json'):
 old.extend(json.loads(p.read_text()).get('records',[]))
used_urls={str(x.get('photo_url','')).split('?')[0] for x in old}
used_hashes={str(x.get('photo_sha256','')) for x in old}
sources=['https://www.xchehang.com/inventory.html','https://ezautoglobal.com/en/cars','https://goldenlaneauto.com/used-cars/']
sess=requests.Session();sess.headers.update({'User-Agent':'Mozilla/5.0 (compatible; PapAutoResearch/1.0)'})
def get(url):r=sess.get(url,timeout=20);r.raise_for_status();return r
def collect(src):
 try:
  soup=bs4.BeautifulSoup(get(src).text,'html.parser')
  pairs=[]
  for img in soup.select('img'):
   u=img.get('data-src') or img.get('src') or ''
   u=urljoin(src,u)
   if not u.startswith('https://') or u.split('?')[0] in used_urls:continue
   if not re.search(r'\\.(?:jpg|jpeg|webp|png)(?:\\?|$)',u,re.I):continue
   if any(w in u.lower() for w in ['logo','icon','banner','avatar','flag','placeholder','sprite']):continue
   card=img.find_parent(['article','li','div'])
   title=(card.get_text(' ',strip=True) if card else img.get('alt','')).strip()[:240]
   if len(title)<8:continue
   pairs.append((src,u,title))
  return pairs
 except Exception as e:print('SOURCE_ERROR',src,str(e));return []
pairs=[]
for src in sources:pairs.extend(collect(src))
print('Candidate photo URLs',len(pairs),flush=True)
def inspect(t):
 src,u,title=t
 try:
  data=get(u).content
  im=Image.open(io.BytesIO(data)).convert('RGB')
  if im.width<600 or im.height<350:return None
  sha=hashlib.sha256(data).hexdigest()
  if sha in used_hashes:return None
  return {'source':src,'photo_url':u,'title_from_supplier_page':title,'photo_sha256':sha,'width':im.width,'height':im.height,'status':'visual_review_required','document_verified':False},im
 except Exception:return None
seen=set();rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 for result in pool.map(inspect,pairs[:500]):
  if result is None:continue
  row,im=result
  if row['photo_sha256'] in seen:continue
  seen.add(row['photo_sha256'])
  idx=len(rows)+1
  name=f'{idx:03d}.jpg';im.thumbnail((900,650));im.save(out/name,quality=90)
  row['file']=name;rows.append(row)
  if len(rows)>=30:break
(out/'manifest.json').write_text(json.dumps({'target':30,'found':len(rows),'records':rows,'not_approved_for_publication':True},ensure_ascii=False,indent=2))
if rows:
 font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
 for start in range(0,len(rows),5):
  chunk=rows[start:start+5];sheet=Image.new('RGB',(1000,260*len(chunk)),'#f7f3eb');draw=ImageDraw.Draw(sheet)
  for j,r in enumerate(chunk):
   im=Image.open(out/r['file']);im.thumbnail((620,215));sheet.paste(im,(5,j*260+30))
   draw.text((630,j*260+15),f'{start+j+1}: {r["title_from_supplier_page"][:32]}',fill='black',font=font)
   draw.text((630,j*260+65),urlparse(r['source']).hostname or '',fill='black',font=font)
  sheet.save(out/f'contact-{start//5:02d}.jpg',quality=85)
print('Distinct supplier photo candidates:',len(rows),flush=True)
