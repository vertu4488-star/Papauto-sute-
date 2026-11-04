#!/usr/bin/env python3
"""Imports public finished auction results; never fabricates sales or photos."""
import datetime as dt
import json,re,time
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup
BASE="https://japancarimportdirect.com/en/auction-statistics/"
def records(html):
    root=BeautifulSoup(html,"html.parser")
    results={}
    brands=["MERCEDES BENZ","LAND ROVER","TOYOTA","HONDA","NISSAN","DAIHATSU","SUZUKI","MAZDA","SUBARU","MITSUBISHI","LEXUS","BMW","VOLKSWAGEN","HINO","ISUZU","AUDI","PEUGEOT","MINI"]
    for a in root.select('a[href*="auction-result"]'):
        url=urljoin(BASE,a.get("href",""))
        path=urlparse(url).path
        if not re.search(r"/auction-statistics/[^/]+-auction-result-[^/]+/?$",path):continue
        slug=path.rstrip("/").split("/")[-1]
        head=re.match(r"(19\\d\\d|20\\d\\d)-(.+?)-auction-result-",slug)
        if not head:continue
        name=re.sub(r"-\\d+$","",head.group(2)).replace("-"," ").upper()
        make_model=None
        for brand in sorted(brands,key=len,reverse=True):
            if name.startswith(brand+" "):make_model=(brand.title(),name[len(brand):].strip().title());break
        if not make_model:
            tokens=name.split(" ",1)
            if len(tokens)!=2:continue
            make_model=(tokens[0].title(),tokens[1].title())
        tile=None
        for parent in [a,*list(a.parents)[:6]]:
            links=parent.select('a[href*="auction-result"]')
            # Reject a parent that spans multiple different lot cards.
            if len(set(x.get("href","") for x in links))>1:continue
            t=parent.get_text(" ",strip=True)
            if 30<len(t)<1100 and "Final price" in t and "km" in t and "€" in t:
                tile=t;break
        if not tile:continue
        date=re.search(r"(\\d{1,2})/(\\d{1,2})/(20\\d\\d)",tile)
        year=re.search(r"\\b(19\\d\\d|20\\d\\d)\\s*[·•]\\s*([\\d,]+)\\s*km",tile)
        price=re.search(r"€\\s*([\\d,]+)\\s*Final\\s+price",tile,re.I)
        if not(date and year and price):continue
        try:sold=dt.date(int(date.group(3)),int(date.group(1)),int(date.group(2))).isoformat()
        except ValueError:continue
        if sold>dt.date.today().isoformat():continue
        mileage=int(year.group(2).replace(",",""))
        amount=int(price.group(1).replace(",",""))
        if amount<=0 or mileage>2000000:continue
        if int(year.group(1))!=int(head.group(1)):continue
        grade=re.search(r"Auction grade\\s*(S|RA?|[0-6](?:\\.5)?)\\b",tile,re.I)
        make,model=make_model
        results[url]=dict(id="jci-"+slug[-85:],country="japan",make=make,model=model,year=int(year.group(1)),mileage=mileage,grade=grade.group(1).upper() if grade else "",auction="Japanese auction",lot="",sold_date=sold,price=amount,currency="EUR",status="sold",source="Japan Car Import Direct · итоговая цена в EUR по курсу источника",source_url=url,photos=[],sheet_url="")
    return list(results.values())

def main():
    s=requests.Session();s.headers["User-Agent"]="PapAutoMarketResearch/1.0 (public historical statistics)"
    rows={}
    for page in range(1,41):
        r=s.get(BASE,params={"page":page} if page>1 else None,timeout=25)
        if r.status_code in (401,403,429):raise SystemExit("Source denies automated access; no data published")
        r.raise_for_status()
        found=records(r.text)
        print("Page",page,"parsed",len(found),flush=True)
        if not found:break
        for x in found:rows[x["source_url"]]=x
        if len(rows)>=500:break
        time.sleep(1.5)
    if len(rows)<500:raise SystemExit("Not publishing incomplete/unverifiable import: "+str(len(rows)))
    dst=Path("data/jp-direct-sold.json");dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(dict(updated_at=dt.date.today().isoformat(),coverage="500 individual sold Japanese auction result cards, converted to EUR by the source, not JPY; illustrative photos of other cars are labelled separately.",lots=list(rows.values())[:500]),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Imported 500 source-linked sold records")
if __name__=="__main__":main()
