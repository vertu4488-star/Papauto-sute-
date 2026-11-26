"""Read-only ATP sourcing. No publication, no source media modification."""
import requests, bs4, re, json, hashlib, io, concurrent.futures, time
from pathlib import Path
from urllib.parse import urljoin,urlparse
from PIL import Image,ImageDraw,ImageFont
from collections import Counter,defaultdict
BASE="https://atp-auto.ru"; out=Path("japan-final15-review");out.mkdir(exist_ok=True)
def norm(x):return re.sub(r"[^a-z0-9+]","",str(x or "").casefold())
def lotkey(a,d,l):return (norm(a),str(d or "")[:10],str(l or "").lstrip("0"))
oldkeys=set();oldurls=set();oldyears=defaultdict(set);oldhash=set()
def row(r):
 if not isinstance(r,dict):return
 title=r.get("title") or r.get("model") or ""
 if r.get("make") and not norm(title).startswith(norm(r["make"])):title=r["make"]+" "+title
 y=r.get("year")
 if y:oldyears[norm(re.sub(r"\b(?:19|20)\d{2}\b.*$","",str(title)))].add(int(y))
 k=lotkey(r.get("auction"),r.get("auction_date") or r.get("date"),r.get("lot") or r.get("lot_number"))
 if all(k):oldkeys.add(k)
 for key in ("source_listing","source_url","url","source"):
  u=r.get(key)
  if isinstance(u,str) and "atp-auto.ru/avto-iz-yaponii/" in u:oldurls.add(u.rstrip("/"))
for p in list(Path("research").glob("owner-*.json"))+[Path("research/atp-japan13-frozen-manifest-20261126.json"),Path("research/atp-seo-33-reference-facts-20261126.json"),Path("render-public/data/gallery-lots.json")]:
 try:
  j=json.loads(p.read_text())
  for r in j if isinstance(j,list) else j.get("lots",j.get("rows",[])):row(r)
 except Exception:pass
for p in Path("assets").rglob("*"):
 if p.is_file() and p.suffix.lower() in (".jpg",".jpeg",".png",".webp"):oldhash.add(hashlib.sha256(p.read_bytes()).hexdigest())
for r in json.loads(Path("/tmp/atp-first/manifest.json").read_text()):
 oldkeys.add(tuple(r["key"]));oldurls.add(r["url"].rstrip("/"))
 for m in r["media"]:oldhash.add(m["sha256"])
print("Existing exact keys",len(oldkeys),"URLs",len(oldurls),"media hashes",len(oldhash),flush=True)
models=[
 ("toyota","wish","Toyota Wish"),("honda","freed-plus","Honda Freed+"),("suzuki","jimny-sierra","Suzuki Jimny Sierra"),("daihatsu","thor","Daihatsu Thor"),
 ("toyota","corolla-fielder","Toyota Corolla Fielder"),("toyota","sienta","Toyota Sienta"),("toyota","tank","Toyota Tank"),("toyota","vitz","Toyota Vitz"),("toyota","roomy","Toyota Roomy"),("toyota","probox","Toyota Probox"),("honda","fit","Honda Fit"),("honda","freed","Honda Freed"),("honda","shuttle","Honda Shuttle"),("honda","vezel","Honda Vezel"),("honda","n-box","Honda N-BOX"),("nissan","nv200","Nissan NV200"),("nissan","juke","Nissan Juke"),("nissan","note","Nissan Note"),("nissan","dayz","Nissan Dayz"),("suzuki","solio","Suzuki Solio"),("suzuki","hustler","Suzuki Hustler"),("suzuki","swift","Suzuki Swift"),("mazda","mazda3","Mazda Mazda3"),("mazda","cx-3","Mazda CX-3"),("mazda","demio","Mazda Demio"),("toyota","noah","Toyota Noah"),("toyota","voxy","Toyota Voxy"),("honda","step-wagon","Honda Stepwgn"),("toyota","raize","Toyota Raize"),("toyota","yaris","Toyota Yaris"),("toyota","yaris-cross","Toyota Yaris Cross")]
aliases={"hondafreed+":{"hondafreed+","hondafreedplus"},"hondastepwgn":{"hondastepwgn","hondastepwagon"},"nissannv200":{"nissannv200","nissannv200vanette"},"mazdamazda3":{"mazda3","mazdamazda3","mazdamazda3fastback","mazdamazda3sedan","mazda3fastback","mazda3sedan"},"toyotacorollafielder":{"toyotacorollafielder"}}
def match(title,expected):
 n=norm(re.sub(r"\b(?:19|20)\d{2}\b.*$","",title));e=norm(expected)
 return n in aliases.get(e,{e})
def get(u):
 r=requests.get(u,timeout=12,headers={"User-Agent":"Mozilla/5.0"});r.raise_for_status();return r
def discover(m):
 b,slug,name=m; cats=[f"{BASE}/avto-iz-yaponii/{b}/{slug}/"]
 if name=="Honda Freed+":cats += [f"{BASE}/avto-iz-yaponii/honda/freed%2B/",f"{BASE}/avto-iz-yaponii/honda/freed+/"]
 if name=="Mazda Mazda3":cats += [f"{BASE}/avto-iz-yaponii/mazda/mazda-3/"]
 links=[]
 for cat in cats:
  for page in (4,5,6,7,8,9,10):
   try:
    r=get(cat+("?PAGE="+str(page) if page>1 else ""));s=bs4.BeautifulSoup(r.text,"html.parser");prefix=urlparse(r.url).path.rstrip("/")+"/"
    if len(prefix.strip("/").split("/"))!=3:continue
    for a in s.select("a[href]"):
     u=urljoin(cat,a["href"]).split("?")[0];p=urlparse(u)
     if p.hostname=="atp-auto.ru" and p.path.startswith(prefix) and re.fullmatch(r"[a-zA-Z0-9]{6,30}/?",p.path[len(prefix):]) and u.rstrip("/") not in oldurls and u not in links:links.append(u)
   except Exception:pass
  if len(links)>=35:break
 print("MODEL",name,"new URLs",len(links),flush=True)
 return m,links[:35]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:groups=list(ex.map(discover,models))
def field(lines,n):return next((lines[i+1] for i,t in enumerate(lines[:-1]) if t.strip().rstrip(":")==n),"")
def detail(item):
 m,u=item;b,slug,name=m
 try:
  s=bs4.BeautifulSoup(get(u).text,"html.parser");title=s.find("h1").get_text(" ",strip=True)
  if not match(title,name):return
  y=int(re.search(r"\b(?:19|20)\d{2}\b",title).group())
  lines=list(s.stripped_strings);f={k:field(lines,k) for k in ["Кузов","Объем","Пробег","Комплектация","Номер лота","Оценка","Аукцион","Дата аукциона","Статус","Цена продажи в Японии","Мощность","Привод","КПП","Цвет"]}
  k=lotkey(f["Аукцион"],f["Дата аукциона"],f["Номер лота"])
  if not all(k) or k in oldkeys or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",k[1]) or f["Статус"].lower()!="sold" or not all(f[n] for n in ("Пробег","Оценка","Объем","Кузов","Цена продажи в Японии")):return
  if not re.fullmatch(r"[3456](?:\.[05])?",f["Оценка"]) or float(f["Оценка"])<3.5:return
  cc=int(re.sub(r"\D","",f["Объем"]) or 0);price=int(re.sub(r"\D","",f["Цена продажи в Японии"]) or 0)
  if cc<500 or cc>2000 or price<=0:return
  pics=[];sheets=[]
  for im in s.select("img[alt]"):
   alt=im.get("alt","").lower()
   if not match(alt,name) or not ("фото с аукциона" in alt or "аукционный лист" in alt):continue
   a=im.find_parent("a",href=True);src=next((urljoin(u,x) for x in [a.get("href") if a else None,im.get("data-src"),im.get("src")] if x and urlparse(urljoin(u,x)).hostname=="7.tru.ru"),None)
   if src:
    target=sheets if "аукционный лист" in alt else pics
    if src not in target:target.append(src)
  if len(pics)<2 or len(sheets)!=1:return
  # Reject the common 314x450 damage diagram early; inspect every accepted original visually later.
  def download(src,kind):
   blob=get(src).content;im=Image.open(io.BytesIO(blob));im.load();w,h=im.size
   sha=hashlib.sha256(blob).hexdigest()
   if min(w,h)<(550 if kind=="sheet" else 280) or sha in oldhash:return
   ext={"JPEG":"jpg","PNG":"png","WEBP":"webp"}.get(im.format)
   if ext:return (blob,{"kind":kind,"source":src,"width":w,"height":h,"sha256":sha,"ext":ext})
  sh=download(sheets[0],"sheet")
  if not sh:return
  photos=[]
  for src in pics[:4]:
   try:
    p=download(src,"vehicle")
    if p and p[1]["sha256"] not in [q[1]["sha256"] for q in photos]:photos.append(p)
   except Exception:pass
  if len(photos)<2:return
  return {"model":name,"title":title,"year":y,"url":u,"facts":f,"key":k,"new_year":y not in oldyears[norm(name)]},photos+[sh]
 except Exception:return
# Interleave model detail links and prefer diversity; stop only after a generous review pool.
items=[(m,ls[i]) for i in range(35) for m,ls in groups if i<len(ls)]
seen=set(oldkeys);hashes=set(oldhash);rows=[];counts=Counter();years=Counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
 for start in range(0,len(items),48):
  for result in ex.map(detail,items[start:start+48]):
   if not result:continue
   r,media=result;k=tuple(r["key"]);my=(r["model"],r["year"])
   if k in seen or counts[r["model"]]>=6 or years[my]>=2 or any(x[1]["sha256"] in hashes for x in media):continue
   seen.add(k);counts[r["model"]]+=1;years[my]+=1;r["index"]=len(rows)+1;r["media"]=[]
   for i,(blob,meta) in enumerate(media):
    filename=f'{r["index"]:03d}-{i}-{meta["kind"]}.{meta["ext"]}'
    (out/filename).write_bytes(blob);meta["file"]=filename;r["media"].append(meta);hashes.add(meta["sha256"])
   rows.append(r)
  print("REVIEW candidates",len(rows),"after",start+48,flush=True)
  if len(rows)>=40:break
(out/"manifest.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2))
(out/"inventory.json").write_text(json.dumps({"old_keys":len(oldkeys),"old_urls":len(oldurls),"existing_model_years":{k:sorted(v) for k,v in oldyears.items()},"models":dict(counts),"scanned_urls":len(items)},ensure_ascii=False,indent=2))
print("COMPLETE CANDIDATES",len(rows),flush=True)
