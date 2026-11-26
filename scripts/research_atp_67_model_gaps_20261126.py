"""Private exact-listing collection. No release, no watermark edits, no bypass."""
import concurrent.futures, hashlib, io, json, re
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests, bs4
from PIL import Image, ImageDraw, ImageFont

OUT=Path("atp-67-private-review")
OUT.mkdir(exist_ok=True)
rows=json.loads(Path("research/atp-67-owner-candidate-queue-20261126.json").read_text())["rows"]
def get(url):
    # Same ordinary HTTP retrieval used by prior Japanese review workflow.
    # Respect source access denials; no proxy, credential or repeated attempts.
    response=requests.get(url,timeout=18)
    response.raise_for_status()
    return response
def field(lines,*names):
    for i,t in enumerate(lines[:-1]):
        if t.strip().rstrip(":") in names:
            return lines[i+1].strip()
    return ""
def collect(r):
    r=dict(r,rights_confirmed=False,publication_ready=False,visual_review_confirmed=False,media=[])
    if not r["exact_listing"]:
        r["status"]="missing_exact_listing"
        return r
    try:
        source=r["url"]
        response=get(source)
        if urlparse(response.url).path.rstrip("/")!=urlparse(source).path.rstrip("/"):
            raise ValueError("listing redirect")
        soup=bs4.BeautifulSoup(response.text,"html.parser")
        h=soup.find("h1")
        if not h: raise ValueError("missing H1")
        title=h.get_text(" ",strip=True)
        year=re.search(r"\b(?:19|20)\d{2}\b",title)
        if not year: raise ValueError("missing exact year")
        lines=list(soup.stripped_strings)
        r.update(title=title,year=int(year.group()),mileage=field(lines,"Пробег"),engine=field(lines,"Объем двигателя","Объём двигателя","Объем"),trim=field(lines,"Комплектация"),lot=field(lines,"Номер лота"),source_price=field(lines,"Стоимость в Корее","Стоимость в Китае","Цена продажи в Японии"),grade=field(lines,"Оценка"),auction=field(lines,"Аукцион"),auction_date=field(lines,"Дата аукциона"))
        # Only vehicle-gallery media before the first price/specification section.
        # Exclude related recommendations and generic inspection diagrams.
        images=[]
        for im in soup.find_all("img"):
            alt=(im.get("alt") or "").lower()
            if "аукционный лист" in alt or "фото с аукциона" in alt:
                kind="sheet" if "аукционный лист" in alt else "vehicle"
            elif any(x in alt for x in ("фото автомобиля","фотография автомобиля","фото машины","ракурс","фото авто")):
                kind="vehicle"
            else:
                continue
            a=im.find_parent("a",href=True)
            candidates=[a.get("href") if a else None,im.get("data-src"),im.get("src")]
            src=next((urljoin(source,x) for x in candidates if x and urlparse(urljoin(source,x)).hostname=="7.tru.ru"),None)
            if src and (src,kind) not in images: images.append((src,kind))
        # On Korean/Chinese detail templates the first image gallery may lack alt.
        # Locate it before the first spec label, not on the rest of the page.
        if not any(k=="vehicle" for _,k in images):
            for el in h.next_elements:
                if isinstance(el,bs4.NavigableString) and str(el).strip() in {"Объем двигателя","Объём двигателя","Пробег","Цена проходного автомобиля","Характеристики","Объем"}: break
                if not isinstance(el,bs4.Tag) or el.name!="img": continue
                a=el.find_parent("a",href=True)
                for x in [a.get("href") if a else None,el.get("data-src"),el.get("src")]:
                    if not x: continue
                    src=urljoin(source,x)
                    if urlparse(src).hostname=="7.tru.ru":
                        if (src,"vehicle") not in images: images.append((src,"vehicle"))
                        break
                if len(images)>=4:break
        if not images: raise ValueError("no identifiable original gallery images")
        seen=set(); chosen=[(u,k) for u,k in images if k=="vehicle"][:2]+[(u,k) for u,k in images if k=="sheet"][:1]
        for j,(u,k) in enumerate(chosen):
            b=get(u).content
            with Image.open(io.BytesIO(b)) as im:
                im.load()
                if min(im.size)<180: raise ValueError("image too small")
                fmt=im.format
            sha=hashlib.sha256(b).hexdigest()
            if sha in seen: continue
            seen.add(sha)
            ext={"JPEG":"jpg","PNG":"png","WEBP":"webp"}.get(fmt)
            if not ext: raise ValueError("unexpected image format")
            filename=f'{r["review_number"]:03d}-{j}-{k}.{ext}'
            (OUT/filename).write_bytes(b)
            r["media"].append({"file":filename,"source":u,"sha256":sha,"kind":k})
        r["status"]="media_collected_private_review" if r["media"] else "no_media"
    except Exception as exc:
        r["status"]="blocked_or_incomplete"
        r["error"]=str(exc)[:300]
    print(r["review_number"],r["status"],len(r["media"]),r.get("error",""),flush=True)
    return r
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    result=list(pool.map(collect,rows))
(OUT/"manifest.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
good=[r for r in result if r["media"]]
font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",17)
for offset in range(0,len(good),8):
    subset=good[offset:offset+8]
    canvas=Image.new("RGB",(1200,220*len(subset)),"#f7f3eb"); d=ImageDraw.Draw(canvas)
    for i,r in enumerate(subset):
        y=i*220; d.text((12,y+5),f'{r["review_number"]:03d} | {r.get("title","")} | {r.get("mileage","")}',font=font,fill="#222222")
        for j,media in enumerate(r["media"][:3]):
            with Image.open(OUT/media["file"]) as photo:
                photo=photo.convert("RGB");photo.thumbnail((390,185));canvas.paste(photo,(j*400+(400-photo.width)//2,y+30))
    canvas.save(OUT/f"contact-{offset//8:02d}.jpg",quality=88)
print("ATP67_PRIVATE_REVIEW",json.dumps({"queue":len(result),"exact":sum(r["exact_listing"] for r in result),"with_media":len(good),"full_photo_pairs":sum(sum(m["kind"]=="vehicle" for m in r["media"])>=2 for r in result),"published":0}),flush=True)
