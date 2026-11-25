"""Private research of exact China-market supplier cars, no release or license claims."""
import re,json,hashlib,io,concurrent.futures
from pathlib import Path
from urllib.parse import urljoin,urlparse
from collections import Counter
import requests
from bs4 import BeautifulSoup
from PIL import Image,ImageDraw,ImageFont
OUT=Path("china-gap-review");OUT.mkdir(exist_ok=True)
BASE="https://chinausedcar.net"
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
prior_urls=set();prior_hashes=set()
for p in Path("research").glob("owner-approved-china*.json"):
 try:
  j=json.loads(p.read_text())
  for r in j.get("records",[]):
   prior_urls.add(r.get("photo_url"));prior_hashes.add(r.get("photo_sha256"))
 except Exception:pass
for p in Path("assets/china-order").rglob("*.jpg"):
 prior_hashes.add(hashlib.sha256(p.read_bytes()).hexdigest())
def get(u):
 r=requests.get(u,timeout=20,headers={"User-Agent":"Mozilla/5.0"});r.raise_for_status();return r
seeds=[]
for brand in ["Byd","Geely","Changan","Haval","Chery","Aion","GAC","Smart"]:
 for page in range(1,4):
  seeds.append(BASE+"/models?brand="+brand+"&page="+str(page))
seeds.extend(BASE+"/brand/"+b for b in ["byd","geely","changan","haval","chery","aion","gac"])
def discover(u):
 try:
  soup=BeautifulSoup(get(u).text,"html.parser");out=[]
  for a in soup.select('a[href*="/model/"]'):
   href=urljoin(u,a["href"]).split("?")[0]
   if urlparse(href).hostname not in {"chinausedcar.net","www.chinausedcar.net"}:continue
   title=a.get_text(" ",strip=True)
   # Only identify exact title or slug here, never use adjacent cards' metadata.
   slug=urlparse(href).path.split("/")[-1].replace("-"," ")
   k=match(title) or match(slug)
   if k:out.append((k,href))
  return out
 except Exception as e:print("DISCOVERY_HOLD",u,str(e)[:120]);return []
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 pairs=list(dict.fromkeys(x for group in pool.map(discover,seeds) for x in group))
print("CHINA_DISCOVERED",Counter(k for k,u in pairs),flush=True)
def inspect(pair):
 k,u=pair
 try:
  soup=BeautifulSoup(get(u).text,"html.parser")
  h=soup.find("h1")
  if not h:return None
  title=h.get_text(" ",strip=True)
  if match(title)!=k:
   print("HOLD_TITLE",k,title[:120]);return None
  content=soup.get_text(" ",strip=True)
  # Record raw source fields, do not infer year, fuel, or FOB from title.
  prices=list(dict.fromkeys(re.findall(r"(?:US\s*\$|USD\s*\$?|\$)\s*[\d,]+(?:\.\d+)?",content)))
  kms=list(dict.fromkeys(re.findall(r"\b[\d,]+\s*km\b",content,re.I)))
  if not prices or not kms:print("HOLD_FIELDS",k,u);return None
  images=[]
  for img in soup.select("img"):
   alt=img.get("alt","")
   if not alt or match(alt)!=k:continue
   src=img.get("data-src") or img.get("src")
   if src:images.append(urljoin(u,src))
  og=soup.select_one('meta[property="og:image"]')
  if og and og.get("content"):images.append(urljoin(u,og["content"]))
  images=list(dict.fromkeys(x for x in images if x.startswith("https://") and x not in prior_urls and not re.search(r"logo|icon|placeholder|default|\\.svg",x,re.I)))
  if not images:return None
  for src in images[:4]:
   try:
    raw=get(src).content;sha=hashlib.sha256(raw).hexdigest()
    if sha in prior_hashes:continue
    im=Image.open(io.BytesIO(raw)).convert("RGB")
    if min(im.size)<350:continue
    # Source image not visually certified: contact sheet only, hold pending human review.
    return dict(model_id="china-"+k,title=title,source=u,photo_url=src,raw_sha256=sha,price_strings=prices[:8],mileage_strings=kms[:8],source_text=content[:12000],rights_confirmed=False,photo_reviewed=False,inspection_report_verified=False,owner_approved=False,publish_state="HOLD"),im
   except Exception:continue
 except Exception as e:print("DETAIL_HOLD",u,str(e)[:100])
 return None
grouped={k:[p for p in pairs if p[0]==k][:5] for k,_ in PATTERNS}
ordered=[grouped[k][i] for i in range(5) for k,_ in PATTERNS if i<len(grouped[k])]
rows=[];seen=set();counts=Counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
 for result in pool.map(inspect,ordered):
  if not result:continue
  r,im=result;k=r["model_id"]
  if counts[k]>=3 or r["raw_sha256"] in seen:continue
  seen.add(r["raw_sha256"]);counts[k]+=1
  name=f"{len(rows)+1:03d}.jpg";im.save(OUT/name,quality=95)
  r["file"]=name;r["jpeg_sha256"]=hashlib.sha256((OUT/name).read_bytes()).hexdigest();rows.append(r)
(OUT/"manifest.json").write_text(json.dumps({"status":"HOLD","records":rows},ensure_ascii=False,indent=2))
font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",18)
for off in range(0,len(rows),9):
 chunk=rows[off:off+9];canvas=Image.new("RGB",(1200,280*((len(chunk)+2)//3)),"#f7f3eb");d=ImageDraw.Draw(canvas)
 for i,r in enumerate(chunk):
  x=i%3*400;y=i//3*280;im=Image.open(OUT/r["file"]);im.thumbnail((390,225))
  canvas.paste(im,(x+(400-im.width)//2,y+28));d.text((x+6,y+4),r["file"]+" "+r["model_id"][6:][:30],font=font,fill="#222")
 canvas.save(OUT/f"contact-{off//9:02d}.jpg",quality=90)
print("CHINA_GAP_RESEARCH_COUNTS",json.dumps(counts),flush=True)
