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
    root=BeautifulSoup(html,"html.parser"); out=[]
    for a in root.select('a[href*="auction-result"]'):
        url=urljoin(BASE,a.get("href",""))
        if not re.search(r"/auction-statistics/[^/]+-auction-result-[^/]+/?$",urlparse(url).path):continue
        for p in [a,*list(a.parents)[:5]]:
            t=p.get_text(" ",strip=True)
            if 30<len(t)<1300 and "Final price" in t and "km" in t and "€" in t:break
        else:continue
        date=re.search(r"(\d{1,2})/(\d{1,2})/(202\d)",t)
        year=re.search(r"\b(19\d\d|20\d\d)\s*[·,]\s*([\d,]+)\s*km",t)
        price=re.search(r"€\s*([\d,]+)\s*Final price",t,re.I)
        if not (date and year and price):continue
        m,d,y=map(int,date.groups())
        try:sold=dt.date(y,m,d).isoformat()
        except ValueError:continue
        if sold>dt.date.today().isoformat():continue
        name=re.search(r"\b(?:19|20)\d\d\s+([A-Z][A-Z0-9 -]{3,85}?)(?=\s+(?:19|20)\d\d\s*[·,])",t)
        if not name:continue
        make,_,model=name.group(1).strip().partition(" ")
        if not model:continue
        grade=re.search(r"Auction grade\s*(S|RA?|[0-6](?:\.5)?)\b",t,re.I)
        price_eur=int(price.group(1).replace(",",""))
        if price_eur<=0:continue
        slug=urlparse(url).path.rstrip("/").split("/")[-1]
        out.append(dict(id="jci-"+slug[-60:],country="japan",make=make.title(),model=model.title(),year=int(year.group(1)),mileage=int(year.group(2).replace(",","")),grade=grade.group(1).upper() if grade else "",auction="Japanese auction",lot="",sold_date=sold,price=price_eur,currency="EUR",status="sold",source="Japan Car Import Direct · итоговая цена в EUR по курсу источника",source_url=url,photos=[],sheet_url=""))
    return out
def main():
    s=requests.Session();s.headers["User-Agent"]="PapAutoMarketResearch/1.0 (public historical statistics)"
    rows={}
    for page in range(1,41):
        r=s.get(BASE,params={"page":page} if page>1 else None,timeout=25)
        if r.status_code in (401,403,429):break
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
