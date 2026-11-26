"""Collect real ATP Japanese auction samples for the exact requested 13 model names."""
import concurrent.futures, hashlib, io, json, re
from pathlib import Path
from urllib.parse import urljoin,urlparse,unquote
import requests, bs4
from PIL import Image,ImageDraw,ImageFont
OUT=Path("atp-japan13-review"); OUT.mkdir(exist_ok=True)
BASE="https://atp-auto.ru"
rows=json.loads(Path("research/atp-japan13-queue-20261126.json").read_text())["rows"]
# Compare original media bytes with existing public asset collection.
existing=set()
for p in Path("assets").rglob("*"):
    if p.is_file() and p.suffix.lower() in (".jpg",".jpeg",".png",".webp"):
        existing.add(hashlib.sha256(p.read_bytes()).hexdigest())
def get(url):
    r=requests.get(url,timeout=18)
    r.raise_for_status()
    return r
def norm(s): return re.sub(r"[^a-z0-9+]","",s.lower())
def matching(row,title):
    val=norm(re.sub(r"\b(?:19|20)\d{2}\b.*$","",title))
    expected=norm(row["model"])
    aliases={"hondastepwgn":{"hondastepwgn","hondastepwagon"},"nissannv200":{"nissannv200","nissannv200vanette"},"mazda3":{"mazda3","mazdamazda3","mazdamazda3fastback","mazdamazda3sedan","mazda3fastback","mazda3sedan"},"hondafreed+":{"hondafreed+","hondafreedplus"}}
    return val in aliases.get(expected,{expected})
def field(lines,*names):
    for i,t in enumerate(lines[:-1]):
        if t.strip().rstrip(":") in names: return lines[i+1].strip()
    return ""
def candidates(row):
    seen=set()
    for u in row["urls"]:
        if u not in seen: seen.add(u);yield u
    base=f'{BASE}/avto-iz-yaponii/{row["brand"]}/'
    # Discover exact model routes from actual brand links when URL differs.
    paths=[base+s+"/" for s in row["slugs"]]
    try:
        soup=bs4.BeautifulSoup(get(base).text,"html.parser")
        for a in soup.select("a[href]"):
            href=urljoin(base,a["href"]); parts=urlparse(href).path.strip("/").split("/")
            if len(parts)==3 and parts[:2]==["avto-iz-yaponii",row["brand"]] and matching(row,row["brand"]+" "+a.get_text(" ",strip=True)):
                if href not in paths:paths.insert(0,href)
    except Exception: pass
    for cat in paths:
        try:
            r=get(cat)
            if urlparse(r.url).path.rstrip("/")!=urlparse(cat).path.rstrip("/"):continue
            soup=bs4.BeautifulSoup(r.text,"html.parser")
            prefix=unquote(urlparse(cat).path).rstrip("/")+"/"
            n=0
            for a in soup.select("a[href]"):
                url=urljoin(cat,a["href"]); p=urlparse(url)
                if p.hostname!="atp-auto.ru" or not unquote(p.path).startswith(prefix):continue
                suffix=unquote(p.path)[len(prefix):].strip("/")
                if not re.fullmatch(r"[a-zA-Z0-9]{6,30}",suffix):continue
                if url not in seen:
                    seen.add(url); yield url;n+=1
                if n>=8:break
        except Exception: continue
def collect(row):
    result=dict(row,status="not_found",media=[],attempts=[])
    for url in candidates(row):
        if len(result["attempts"])>=10:break
        try:
            response=get(url)
            if urlparse(response.url).path.rstrip("/")!=urlparse(url).path.rstrip("/"):raise ValueError("redirect")
            soup=bs4.BeautifulSoup(response.text,"html.parser")
            title=soup.find("h1").get_text(" ",strip=True)
            year=re.search(r"\b(?:19|20)\d{2}\b",title)
            if not year or not matching(row,title):raise ValueError("wrong title: "+title)
            lines=list(soup.stripped_strings)
            facts=dict(title=title,year=int(year.group()),mileage=field(lines,"Пробег"),engine=field(lines,"Объем","Объем двигателя","Объём двигателя"),trim=field(lines,"Комплектация"),lot=field(lines,"Номер лота"),grade=field(lines,"Оценка"),auction=field(lines,"Аукцион"),auction_date=field(lines,"Дата аукциона"),sale_status=field(lines,"Статус"),source_price=field(lines,"Цена продажи в Японии"))
            if not all(facts[k] for k in ("mileage","lot","auction","auction_date","grade")):raise ValueError("missing lot facts")
            # Full original sheet and exact vehicle image alt only; no related model thumbnails.
            images=[]
            for im in soup.find_all("img"):
                alt=im.get("alt","")
                if not ("фото с аукциона" in alt.lower() or "аукционный лист" in alt.lower()):continue
                if not matching(row,alt):continue
                kind="sheet" if "аукционный лист" in alt.lower() else "vehicle"
                a=im.find_parent("a",href=True)
                src=next((urljoin(url,x) for x in [a.get("href") if a else None,im.get("data-src"),im.get("src")] if x and urlparse(urljoin(url,x)).hostname=="7.tru.ru"),None)
                if src and (src,kind) not in images:images.append((src,kind))
            chosen=[(u,k) for u,k in images if k=="vehicle"][:2]+[(u,k) for u,k in images if k=="sheet"][:1]
            if not any(k=="vehicle" for u,k in chosen) or not any(k=="sheet" for u,k in chosen):raise ValueError("missing exact photo/full sheet")
            files=[];seen=set()
            for u,kind in chosen:
                b=get(u).content
                with Image.open(io.BytesIO(b)) as im:
                    im.load()
                    if min(im.size)<180:raise ValueError("small image")
                    ext={"JPEG":"jpg","PNG":"png","WEBP":"webp"}.get(im.format)
                if not ext:raise ValueError("bad image type")
                sha=hashlib.sha256(b).hexdigest()
                if sha in seen:continue
                if kind=="vehicle" and sha in existing:raise ValueError("existing exact media")
                seen.add(sha);files.append((b,kind,ext,sha,u))
            if not any(f[1]=="vehicle" for f in files) or not any(f[1]=="sheet" for f in files):raise ValueError("missing unique photo or sheet")
            result.update(facts,url=url,status="ready_for_visual_review")
            for j,(b,k,ext,sha,u) in enumerate(files):
                name=f'{row["number"]:03d}-{j}-{k}.{ext}'
                (OUT/name).write_bytes(b)
                result["media"].append({"file":name,"kind":k,"sha256":sha,"source":u})
            break
        except Exception as e:result["attempts"].append({"url":url,"error":str(e)[:200]})
    print(row["model"],result["status"],len(result["media"]),flush=True)
    return result
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    results=list(pool.map(collect,rows))
(OUT/"manifest.json").write_text(json.dumps(results,ensure_ascii=False,indent=2))
good=[r for r in results if r["media"]]
font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",18)
for off in range(0,len(good),7):
    batch=good[off:off+7];canvas=Image.new("RGB",(1200,240*len(batch)),"#f7f3eb");d=ImageDraw.Draw(canvas)
    for i,r in enumerate(batch):
        y=i*240;d.text((12,y+5),f'{r["number"]:02d} | {r["title"]} | {r["mileage"]} | {r["lot"]}',font=font,fill="#222")
        for j,m in enumerate(r["media"]):
            with Image.open(OUT/m["file"]) as photo:
                photo=photo.convert("RGB");photo.thumbnail((390,200));canvas.paste(photo,(j*400+(400-photo.width)//2,y+32))
    canvas.save(OUT/f"contact-{off//7:02d}.jpg",quality=90)
print("ATP_JAPAN13_REVIEW",json.dumps({"requested":len(results),"complete_photo_sheet":len(good),"published":0}),flush=True)
