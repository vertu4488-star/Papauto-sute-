"""Research-only Xin Che Hang exact supplier examples for gaps in PapAuto China 499.
Never publish from this action. Source titles may contain incorrect fuel or specifications.
No external link is inserted into customer-facing cards.
"""
import requests, bs4, re, hashlib, json, io
from pathlib import Path
from urllib.parse import urljoin
from PIL import Image,ImageDraw,ImageFont
BASE="https://www.xchehang.com/inventory.html"
OUT=Path("china-gap-review");OUT.mkdir(exist_ok=True)
TARGETS=["BYD Song PLUS","BYD Dolphin","BYD Song Pro","Geely Galaxy Galaxy L6",
"BYD Qin PLUS","BYD Yuan PLUS","BYD Seagull","Geely Monjaro","Geely Xingyue L",
"Changan CS35 PLUS","Chery Tiggo 4","Geely Atlas","Geely Cityray","BYD Destroyer 05",
"BYD Qin L","Haval H4","Changan Alsvin","Changan Lumin","GAC Aion Y",
"BYD Song L","Geely Galaxy E5","BYD e2"]
def norm(s):return re.sub(r"[^a-z0-9]+"," ",str(s).lower()).strip()
published=Path("china-order.html").read_text()
used_title={(norm(a),int(y)) for a,y in re.findall(r'<h2>([^<]*?)\s+(20\d\d)</h2>',published)}
old_sha=set()
for p in Path('research').glob('owner-approved-china-supplier*.json'):
 try:
  j=json.loads(p.read_text())
  for r in j.get('records',[]):old_sha.add(r.get('photo_sha256',''))
 except Exception:pass
response=requests.get(BASE,headers={'User-Agent':'Mozilla/5.0'},timeout=40)
response.raise_for_status()
soup=bs4.BeautifulSoup(response.text,'html.parser')
print('inventory response',len(response.content),'headings',len(soup.select('h3')),flush=True)
found=[]
for h in soup.select('h3,h2,h4'):
 title=h.get_text(' ',strip=True)
 yr=re.search(r'\b(20\d\d)\b',title)
 if not yr:continue
 year=int(yr.group(1))
 if year not in (2022,2023,2024,2025):continue
 target=next((t for t in TARGETS if norm(t) in norm(title)),None)
 if not target:continue
 if norm(title)==norm(target):continue
 anchor=None
 for parent in h.parents:
  if parent.name not in ('article','div','li','section'):continue
  text=parent.get_text(' ',strip=True)
  imgs=parent.find_all('img')
  if len(imgs)>=1 and len(text)<1400 and ('FOB' in text or 'km' in text):
   anchor=parent;break
 if anchor is None:continue
 txt=anchor.get_text(' ',strip=True)
 if 'km' not in txt or 'USD' not in txt:continue
 srcs=[]
 for im in anchor.find_all('img'):
  src=im.get('data-src') or im.get('src')
  if not src:continue
  u=urljoin(BASE,src)
  if u not in srcs and u.startswith('https://www.xchehang.com/'):srcs.append(u)
 if not srcs:continue
 if (norm(target),year) in used_title:continue
 found.append(dict(target=target,title=title,year=year,meta=txt[:450],photos=srcs,source_url=BASE))
print('raw targeted family year matches',len(found),flush=True)
seen_pairs=set();seen_shas=set();review=[]
for x in found:
 pair=(norm(x['target']),x['year'])
 if pair in seen_pairs:continue
 try:
  b=requests.get(x['photos'][0],headers={'User-Agent':'Mozilla/5.0'},timeout=25).content
  im=Image.open(io.BytesIO(b)).convert('RGB')
  if min(im.size)<280:continue
  raw_sha=hashlib.sha256(b).hexdigest()
  if raw_sha in seen_shas or raw_sha in old_sha:continue
  seen_pairs.add(pair);seen_shas.add(raw_sha)
  index=len(review)+1;filename=f'{index:02d}.jpg'; im.save(OUT/filename,quality=92)
  review.append(dict(index=index,model_family=x['target'],year=x['year'],source_title=x['title'],source_text=x['meta'],source_url=x['source_url'],source_photo_url=x['photos'][0],image_file=filename,source_photo_sha256=raw_sha,owner_approval=False,third_party_rights_verified=False,inspection_report_verified=False,visual_photo_setting_verified=False,source_fuel_and_drivetrain_unverified=True,publishable=False))
  if len(review)>=20:break
 except Exception as e:print('SKIP PHOTO',x['title'],str(e)[:80])
(OUT/'manifest.json').write_text(json.dumps(dict(source=BASE,records=review,unreviewed_image_approval_required=True),ensure_ascii=False,indent=2))
print('accepted individual photo references',len(review),[(x['model_family'],x['year']) for x in review],flush=True)
if review:
 try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
 except:font=ImageFont.load_default()
 for start in range(0,len(review),10):
  segment=review[start:start+10];w=1200;h=190*len(segment)
  canvas=Image.new('RGB',(w,h),'#f7f3eb');draw=ImageDraw.Draw(canvas)
  for n,rec in enumerate(segment):
   iy=n*190;draw.text((10,iy+5),f"{rec['index']:02d} {rec['source_title'][:63]}",font=font,fill='#242424')
   with Image.open(OUT/rec['image_file']) as im:
    im.thumbnail((1000,155));canvas.paste(im,((w-im.width)//2,iy+30))
  canvas.save(OUT/f'contact-{start//10:02d}.jpg',quality=85)
