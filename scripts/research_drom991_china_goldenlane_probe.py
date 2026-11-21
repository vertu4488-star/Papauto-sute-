"""Visual research of exact GoldenLane supplier unit photos only.
Never put images on public gallery without exact source/rights verification.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
import requests,hashlib,json,io
OUT=Path('china-goldenlane-probe');OUT.mkdir(exist_ok=True)
urls=[
 'https://goldenlaneauto.com/used-cars/byd-yuan-plus-63352/',
 'https://goldenlaneauto.com/used-cars/byd-yuan-plus-87101/',
 'https://goldenlaneauto.com/used-cars/byd-song-max-78241/',
 'https://goldenlaneauto.com/brands/byd/'
]
headers={'User-Agent':'Mozilla/5.0 (compatible; PAPAUTO-research/1.0)'}
records=[]
def h(u):
 r=requests.get(u,timeout=28,headers=headers)
 r.raise_for_status()
 return r
seen=set()
for p,page in enumerate(urls,1):
 try:
  soup=BeautifulSoup(h(page).text,'html.parser')
  imgs=[]
  for im in soup.select('img'):
   for attr in ['data-src','data-lazy-src','src']:
    path=im.get(attr)
    if path and not path.startswith('data:'):
     url=urljoin(page,path)
     if urlparse(url).netloc and url not in imgs:imgs.append(url)
  # The large photo set on product pages is either src or parent anchor; collect separately.
  for im in soup.select('a[href]'):
   u=urljoin(page,im['href'])
   if '/media/' in u or u.lower().split('?')[0].endswith(('.jpg','.jpeg','.webp','.png')):
    if u not in imgs:imgs.append(u)
  print('page',page,'image urls',len(imgs),flush=True)
  saved=0
  for url in imgs[:85]:
   if saved>=9:break
   if any(s in url for s in ['flag-','logo','avatar','favicon','badge','icon','banner','sprite','placeholder']):continue
   try:
    b=h(url).content; im=Image.open(io.BytesIO(b)).convert('RGB')
    if min(im.size)<320: continue
    digest=hashlib.sha256(b).hexdigest()
    if digest in seen:continue
    seen.add(digest)
    saved+=1
    filename=f'page{p}-{saved:02d}.jpg'
    im.save(OUT/filename,quality=90)
    records.append({'page':page,'img':url,'sha256':digest,'image_file':filename,'width':im.width,'height':im.height})
   except Exception as e: print('skip image',str(e)[:70])
 except Exception as e:print('page error',page,str(e)[:90])
(OUT/'manifest.json').write_text(json.dumps(records,indent=2,ensure_ascii=False))
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
for p in range(1,len(urls)+1):
 rr=[x for x in records if x['page']==urls[p-1]]
 if not rr:continue
 canvas=Image.new('RGB',(1100,((len(rr)+2)//3)*290),'#faf7f1');d=ImageDraw.Draw(canvas)
 for idx,r in enumerate(rr):
  x=idx%3*366;y=idx//3*290
  im=Image.open(OUT/r['image_file'])
  im.thumbnail((358,235))
  canvas.paste(im,(x+(366-im.width)//2,y+28))
  d.text((x+6,y+4),r['image_file'],font=font,fill='#272321')
  d.text((x+6,y+265),r['img'].split('/')[-1][:39],font=font,fill='#272321')
 canvas.save(OUT/f'contact-page{p}.jpg',quality=88)
print('probe images',len(records),flush=True)
