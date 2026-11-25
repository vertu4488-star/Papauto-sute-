"""Second private photo-screening pass. Do not publish any candidate."""
import re,json,hashlib,io,concurrent.futures
from pathlib import Path
from urllib.parse import urljoin,urlparse
from collections import Counter
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw,ImageFont
OUT=Path("china-gap-wave2-review");OUT.mkdir(exist_ok=True)
PATTERNS=[
("geely-monjaro",r"\bgeely\b.*\b(?:xingyue\s*l|monjaro)\b"),
("geely-cityray",r"\bgeely\b.*\b(?:boyue\s*cool|cityray)\b"),
("geely-atlas-boyue",r"\bgeely\b.*\b(?:boyue(?!\s*cool)|atlas)\b"),
("geely-galaxy-l6",r"\bgeely\b.*\b(?:galaxy.*)?l6\b"),
("geely-galaxy-e5",r"\bgeely\b.*\b(?:galaxy.*)?(?:e5|ex5)\b"),
("byd-song-plus",r"\bbyd\b.*\bsong\s*plus\b"),
("byd-song-pro",r"\bbyd\b.*\bsong\s*pro\b"),
("byd-dolphin",r"\bbyd\b.*\bdolphin\b"),
("byd-seagull",r"\bbyd\b.*\bseagull\b"),
("byd-yuan-plus-atto-3",r"\bbyd\b.*\b(?:yuan\s*plus|atto\s*3)\b"),
("byd-qin-plus",r"\bbyd\b.*\bqin\s*plus\b"),
("byd-qin-l",r"\bbyd\b.*\bqin\s*l\b"),
("byd-destroyer-05",r"\bbyd\b.*\b(?:destroyer|destroyer\s*05|quzhujian)\s*05\b"),
("byd-song-l",r"\bbyd\b.*\bsong\s*l\b"),
("byd-seal-06",r"\bbyd\b.*\bseal\s*06\b"),
("byd-e2",r"\bbyd\b.*\be2\b"),
("changan-cs35-plus",r"\bchangan\b.*\bcs35\s*plus\b"),
("changan-alsvin",r"\bchangan\b.*\b(?:alsvin|yuexiang)\b"),
("changan-lumin",r"\bchangan\b.*\blumin\b"),
("chery-tiggo-4",r"\bchery\b.*\btiggo\s*4\b"),
("haval-h4",r"\bhaval\b.*\bh4\b"),
("gac-aion-y",r"\baion\b.*\b(?:aion\s*)?y(?:\s*plus)?\b"),
]
def match(s):
 found=[k for k,p in PATTERNS if re.search(p,s,re.I)]
 return found[0] if len(found)==1 else None

DIRECT=[["byd-e2","https://goldenlaneauto.com/used-cars/byd-e2-83167/"],["byd-e2","https://goldenlaneauto.com/used-cars/byd-e2-59606/"],["byd-e2","https://goldenlaneauto.com/used-cars/byd-e2-59303/"],["geely-galaxy-e5","https://goldenlaneauto.com/used-cars/geely-galaxy-e5-88012/"],["geely-galaxy-e5","https://goldenlaneauto.com/used-cars/geely-galaxy-e5-79374/"],["geely-galaxy-e5","https://goldenlaneauto.com/used-cars/geely-galaxy-e5-87986/"],["byd-destroyer-05","https://www.excars.cn/cars/detail/usedcar-byd-destroyer-05-360839"],["byd-destroyer-05","https://www.excars.cn/cars/detail/usedcar-byd-destroyer-05-357545"],["byd-destroyer-05","https://www.eautoexport.com/cars/byd-destroyer-05-2024-y64b3ba8ec99901c"],["changan-cs35-plus","https://zh-cn.eautoexport.com/cars/changan-cs35-plus-2023-exuyeabeef884ece"],["changan-cs35-plus","https://msauto.group/product/ca11-changan-cs35plus-2023"],["byd-song-pro","https://goldenlaneauto.com/used-cars/byd-song-pro-78242/"],["byd-song-pro","https://goldenlaneauto.com/used-cars/byd-song-pro-80227/"],["byd-dolphin","https://goldenlaneauto.com/used-cars/byd-dolphin-87022/"],["byd-dolphin","https://goldenlaneauto.com/used-cars/byd-dolphin-81734/"],["byd-qin-plus","https://goldenlaneauto.com/used-cars/byd-qin-plus-86380/"],["byd-qin-plus","https://goldenlaneauto.com/used-cars/byd-qin-plus-86382/"],["geely-galaxy-e5","https://www.xingyuepaipai.cn/product_382897.html"],["byd-e2","https://hainaauto.com/vehicle/350684772"]]

def get(u):
 r=requests.get(u,timeout=15,headers={"User-Agent":"Mozilla/5.0"});r.raise_for_status();return r
prior=json.loads(Path("/tmp/china-gap-first/manifest.json").read_text())["records"]
firsthash={r["raw_sha256"] for r in prior}
approvedhash={hashlib.sha256(p.read_bytes()).hexdigest() for p in Path("assets/china-order").rglob("*.jpg")}
# Exact source URL, not inferred inventory or stock. GoldenLane category discovery uses exact slug.
def discover(u):
 try:
  soup=BeautifulSoup(get(u).text,"html.parser");out=[]
  for a in soup.select('a[href*="/used-cars/"]'):
   href=urljoin(u,a["href"]).split("?")[0]
   if urlparse(href).hostname!="goldenlaneauto.com":continue
   slug=urlparse(href).path.strip("/").split("/")[-1].replace("-"," ")
   k=match(slug)
   if k:out.append((k,href))
  return out
 except Exception:return []
seeds=["https://goldenlaneauto.com/brands/"+b+"/?lang=en&page="+str(p) for b in ["byd","geely","geely-galaxy","changan","haval","chery","aion"] for p in [1,2,3,4]]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 discovered=list(dict.fromkeys(x for g in pool.map(discover,seeds) for x in g))
pairs=list(dict.fromkeys(DIRECT+discovered))
# Keep a reasonable number of detail pages per model. Existing ChinaUsedCar photos already screened;
# only consider additional original photo URLs in the same verified listing.
grouped={k:[(kk,u) for kk,u in pairs if kk==k][:4] for k,_ in PATTERNS}
pairs=[grouped[k][i] for i in range(4) for k,_ in PATTERNS if i<len(grouped[k])]
pairs.extend((r["model_id"][6:],r["source"]) for r in prior)
pairs=list(dict.fromkeys(pairs))
def inspect(pair):
 k,u=pair
 try:
  soup=BeautifulSoup(get(u).text,"html.parser");h=soup.find("h1")
  if not h:return []
  title=h.get_text(" ",strip=True)
  # GoldenLane H1 sometimes omits brand; require matching model name with explicit URL brand.
  slug=urlparse(u).path.strip("/").split("/")[-1].replace("-"," ")
  if match(title)!=k and match(slug)!=k and (k,u) not in DIRECT:return []
  txt=soup.get_text(" ",strip=True)
  images=[]
  for img in soup.select("img"):
   alt=img.get("alt","");src=img.get("data-src") or img.get("src")
   if not src:continue
   # Exact name or exact same full title; no related models. Context not yet certified.
   if match(alt)==k or (alt and len(alt)>15 and (alt.casefold() in title.casefold() or title.casefold() in alt.casefold())):
    images.append(urljoin(u,src))
  og=soup.select_one('meta[property="og:image"]')
  if og and og.get("content"):images.append(urljoin(u,og["content"]))
  images=list(dict.fromkeys(x for x in images if x.startswith("https://") and not re.search(r"logo|icon|placeholder|default|\.svg",x,re.I)))
  rows=[]
  for src in images[:7]:
   try:
    raw=get(src).content;sha=hashlib.sha256(raw).hexdigest()
    if sha in firsthash or sha in approvedhash:continue
    im=Image.open(io.BytesIO(raw)).convert("RGB")
    if min(im.size)<350:continue
    rows.append((dict(model_id="china-"+k,title=title,source=u,photo_url=src,raw_sha256=sha,source_text=txt[:16000],photo_context_verified=False,rights_confirmed=False,owner_approved=False,publish_state="HOLD"),im))
    if len(rows)>=3:break
   except Exception:continue
  return rows
 except Exception as e:print("HOLD",u,str(e)[:80]);return []
rows=[];seen=set();counts=Counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 for group in pool.map(inspect,pairs):
  for r,im in group:
   if r["raw_sha256"] in seen or counts[r["model_id"]]>=10:continue
   seen.add(r["raw_sha256"]);counts[r["model_id"]]+=1
   name=f"{len(rows)+1:03d}.jpg";im.save(OUT/name,quality=92);r["file"]=name
   r["jpeg_sha256"]=hashlib.sha256((OUT/name).read_bytes()).hexdigest();rows.append(r)
(OUT/"manifest.json").write_text(json.dumps({"status":"HOLD","records":rows},ensure_ascii=False,indent=2))
font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",16)
for off in range(0,len(rows),12):
 chunk=rows[off:off+12];canvas=Image.new("RGB",(1200,250*((len(chunk)+2)//3)),"#f7f3eb");d=ImageDraw.Draw(canvas)
 for i,r in enumerate(chunk):
  x=i%3*400;y=i//3*250;im=Image.open(OUT/r["file"]);im.thumbnail((390,210))
  canvas.paste(im,(x+(400-im.width)//2,y+25));d.text((x+6,y+3),r["file"]+" "+r["model_id"][6:][:32],font=font,fill="#222")
 canvas.save(OUT/f"contact-{off//12:02d}.jpg",quality=88)
print("CHINA_GAP_WAVE2_COUNTS",json.dumps(counts),flush=True)
