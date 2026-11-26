import requests,bs4,re,io,json,hashlib,concurrent.futures
from pathlib import Path
from urllib.parse import urljoin,urlparse
from PIL import Image
out=Path("honda-review");out.mkdir(exist_ok=True)
base="https://atp-auto.ru/avto-iz-yaponii/honda/"
groups={"freed-spike":["9uF2KZ1vJLHlcBH","72ImxU0nfcoFapw","9uMhgktxZAySVF8","7a81FkIFONFi3yH","38h86LrdezsyXYu","7afCsbl2TeFN5k6","4VLvGqBlXD6Kvk"],"step-wagon":["71kgFpXOIkDPpD5","2PIvhIo2dTA1Q4","0wIgroMGvnK4v54","8a47neYTNwn5zW","0m1SGdqR0OIMvwg","6JhzecsgwvLNflj","6JnUxSuqfm2E1w4","Jd3YUKrqmUrRVD"]}
def get(u): 
 r=requests.get(u,timeout=12);r.raise_for_status();return r
def field(lines,n):
 return next((lines[i+1] for i,t in enumerate(lines[:-1]) if t.rstrip(":")==n),"")
def collect(item):
 slug,code=item;u=base+slug+"/"+code+"/"; row={"url":u,"model":slug,"code":code,"media":[]}
 try:
  s=bs4.BeautifulSoup(get(u).text,"html.parser");title=s.find("h1").get_text(" ",strip=True);row["title"]=title
  if slug.replace("-"," ") not in title.lower():raise ValueError("wrong title")
  lines=list(s.stripped_strings)
  for n in ["Кузов","Объем","Пробег","Комплектация","Номер лота","Оценка","Аукцион","Дата аукциона","Статус","Цена продажи в Японии"]:row[n]=field(lines,n)
  imgs=[]
  for im in s.select("img"):
   alt=im.get("alt","").lower()
   if slug.replace("-"," ") not in alt:continue
   if "фото с аукциона" not in alt and "аукционный лист" not in alt:continue
   a=im.find_parent("a",href=True);src=next((urljoin(u,x) for x in [a.get("href") if a else None,im.get("data-src"),im.get("src")] if x and urlparse(urljoin(u,x)).hostname=="7.tru.ru"),None)
   if not src or any(src==x[0] for x in imgs):continue
   imgs.append((src,"sheet" if "аукционный лист" in alt else "vehicle"))
  for i,(src,kind) in enumerate(imgs):
   try:
    b=get(src).content
    with Image.open(io.BytesIO(b)) as im:
     im.load(); w,h=im.size
     if min(w,h)<180:continue
     ext={"JPEG":"jpg","PNG":"png","WEBP":"webp"}.get(im.format)
    if not ext:continue
    # keep alternate frames as supplied, no modification
    name=f"{code}-{i:02d}-{kind}.{ext}";(out/name).write_bytes(b);row["media"].append({"file":name,"kind":kind,"width":w,"height":h,"source":src,"sha256":hashlib.sha256(b).hexdigest()})
   except Exception as e:row.setdefault("errors",[]).append(str(e)[:200])
 except Exception as e:row["error"]=str(e)[:300]
 return row
items=[(slug,code) for slug,codes in groups.items() for code in codes]
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:rows=list(pool.map(collect,items))
(out/"manifest.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2))
print([(x.get("title"),x.get("Номер лота"),len(x["media"])) for x in rows])
