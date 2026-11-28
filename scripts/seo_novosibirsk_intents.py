"""Search-intent navigation from real published model coverage. No invented prices or stock."""
import json,re
from collections import Counter
from html import escape
from pathlib import Path

def e(s):return escape(str(s),quote=True)
HUB={"japan":"avto-iz-yaponii-novosibirsk.html","korea":"avto-iz-korei-novosibirsk.html","china":"avto-iz-kitaya-novosibirsk.html"}
COUNTRY={"japan":"Японии","korea":"Кореи","china":"Китая"}
CAT="catalog-avto-iz-yaponii-novosibirsk.html"
PRICE="stoimost-avto-iz-yaponii-novosibirsk.html"
GENERAL="avto-pod-zakaz-novosibirsk.html"
STYLE='<style>.pa-seo-links{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:8px 18px;padding-left:20px}.pa-seo-links li{min-width:0;overflow-wrap:anywhere}.pa-seo-links small{display:block;color:#625c53}.pa-seo-nav{margin:18px auto;padding:16px;max-width:1060px;box-sizing:border-box}.pa-seo-nav a{overflow-wrap:anywhere}</style>'
def read(p):return p.read_text(encoding="utf-8")
def write(p,s):p.write_text(s,encoding="utf-8")
def add(p,block):
    s=read(p)
    if "</main>" not in s or "</head>" not in s:raise RuntimeError("SEO missing main/head "+str(p))
    write(p,s.replace("</main>",block+"</main>",1).replace("</head>",STYLE+"</head>",1))
def anchor(href,label):return '<a href="/'+e(href)+'">'+e(label)+'</a>'
def section(title,body,id="pa-seo-intent-links"):
    return '<section class="section wrap pa-seo-nav" id="'+id+'"><h2>'+e(title)+'</h2>'+body+'</section>'
def market(r):return "korea" if r["market"]=="south-korea" else r["market"]
def name(r):return r["brand"]+" "+r["model"]
def model_link(r):return anchor("models/"+r["id"]+".html",name(r))
def render(target,coverage,registry):
    items=json.loads(read(target/"data/papauto-expanded-45x3-2026.json"))["items"]
    rep={x["model_id"]:x for x in coverage["models"]}
    assert len(items)==147 and set(rep)=={x["id"] for x in items}
    groups={m:[x for x in items if market(x)==m] for m in HUB}
    assert {m:len(v) for m,v in groups.items()}=={"japan":57,"korea":45,"china":45}
    def model_list(rows):
        result=[]
        for r in sorted(rows,key=lambda x:(x["brand"],x["model"])):
            if not (target/"models"/(r["id"]+".html")).is_file():raise RuntimeError("SEO missing model "+r["id"])
            c=rep[r["id"]];n=c.get("auction_matches",0)
            details=[r.get("engine","Объём уточняется")]
            if n:details.append("архив аукционов: "+str(n))
            if c.get("supplier_matches"):details.append("примеры поставщика: "+str(c["supplier_matches"]))
            if c.get("reference_cards"):details.append("справочные примеры: "+str(c["reference_cards"]))
            result.append("<li>"+model_link(r)+"<small>"+e(" · ".join(details))+"</small></li>")
        return '<ul class="pa-seo-links">'+''.join(result)+'</ul>'
    # Canonical model links on all three regional landing pages, all crawlable HTML.
    for m,rows in groups.items():
        extra='<p>'+anchor(CAT,"Каталог авто из Японии")+" · "+anchor(PRICE,"Стоимость до Новосибирска")+'</p>' if m=="japan" else ""
        add(target/HUB[m],section("Модели авто из "+COUNTRY[m]+" под заказ в Новосибирск",'<p>Выберите модель для сравнения поколений и проверенных примеров. Архив не означает наличие автомобиля.</p>'+model_list(rows)+extra))
    common='<p>'+" · ".join(anchor(HUB[m],"Авто из "+COUNTRY[m]+" в Новосибирск") for m in HUB)+'</p><p>'+anchor(CAT,"Каталог японских автомобилей")+" · "+anchor(PRICE,"Цена авто из Японии под ключ")+" · "+anchor("models-135.html","Все модели")+'</p>'
    common+='<p>'+anchor(GENERAL,"Авто под заказ в Новосибирске")+' · '+anchor(HUB["japan"]+"#pa-commercial-no-russian-mileage","Машины без пробега по РФ")+' · '+anchor(HUB["japan"]+"#pa-commercial-japan-delivery","Как привезти авто из Японии")+' · '+anchor("podbor.html","Индивидуальный подбор")+'</p>'
    for filename in ["index.html","catalog.html",GENERAL,"japan.html","models-novosibirsk.html"]:
        route_map = ''
        if filename == "index.html":
            route_map = '<figure class="pa-delivery-map" style="margin:18px 0 24px;border-radius:18px;overflow:hidden;background:#111c25"><img src="/assets/visual/papauto-delivery-map-20261128.webp" width="1600" height="800" alt="Схема доставки автомобилей из Владивостока через Хабаровск, Читу, Улан-Удэ, Иркутск и Красноярск в Новосибирск" loading="lazy" decoding="async" style="display:block;width:100%;height:auto"><figcaption style="padding:10px 16px;font-size:13px;color:#eee;background:#111c25">Схема маршрута доставки. Фактический маршрут согласуем при заказе.</figcaption></figure>'
        add(target/filename,section("Автомобили под заказ с доставкой в Новосибирск",route_map+common))
    # Preserve existing titles, H1s, canonicals, photo cards and calculators. Add
    # genuinely related model choices and their regional parent, no keyword repetition.
    for r in items:
        m=market(r)
        others=[x for x in groups[m] if x["id"]!=r["id"]]
        others.sort(key=lambda x:(x["brand"]!=r["brand"],-rep[x["id"]].get("auction_matches",0),x["id"]))
        nav='<p>'+anchor(HUB[m],"Подбор и доставка авто из "+COUNTRY[m]+" в Новосибирск")+' · '+anchor("models-135.html","Каталог всех моделей")+'</p><p>'+ " · ".join(model_link(x) for x in others[:5])+'</p>'
        if m=="japan":nav+='<p>'+anchor(CAT,"Каталог японских моделей")+" · "+anchor(PRICE,"Из чего складывается цена под ключ")+'</p>'
        add(target/"models"/(r["id"]+".html"),section("Сравнить другие модели и условия доставки",nav))
    p=target/CAT;s=read(p);s,n=re.subn(r'(<section id="pa-seo-japan-catalog">)[\s\S]*?</section>',lambda m:m.group(1)+'<h2>57 моделей из Японии</h2>'+model_list(groups["japan"])+'</section>',s,count=1);assert n==1
    # Existing screened gallery records only. Prefer diverse popular model names.
    chosen=[];seen=set()
    for r in registry["lots"]:
        amount=r.get("price_jpy",0)
        if r.get("market")!="japan" or r.get("status")!="sold" or not isinstance(amount,(int,float)) or amount<=0 or not r.get("photos") or not r.get("inspection_image"):continue
        if r["model"] in seen:continue
        if not (target/r["photos"][0].lstrip("/")).is_file() or not (target/r["inspection_image"].lstrip("/")).is_file():continue
        if not (target/"lots"/(r["id"]+".html")).is_file():continue
        seen.add(r["model"]);chosen.append(r)
        if len(chosen)>=8:break
    assert len(chosen)>=6
    samples=[];table=[]
    for r in chosen:
        title=r["model"]+" · "+str(r["year"]);amount=f'{int(r["price_jpy"]):,}'.replace(","," ")+" ¥"
        detail=anchor("lots/"+r["id"]+".html",title)
        samples.append('<article><a href="/lots/'+e(r["id"])+'.html"><img loading="lazy" src="'+e(r["photos"][0])+'" alt="'+e(title+" — фото с аукциона")+'"></a><h3>'+detail+'</h3><p>Цена завершённых торгов: '+e(amount)+'</p><p><a href="'+e(r["inspection_image"])+'">Аукционный лист</a></p></article>')
        table.append('<tr><td>'+detail+'</td><td>'+e(r["auction_date"])+'</td><td>'+e(amount)+'</td></tr>')
    s,n=re.subn(r'(<section id="pa-seo-japan-samples">)[\s\S]*?</section>',lambda m:m.group(1)+'<h2>Примеры завершённых аукционов</h2><div class="pa-seo-sample-grid">'+''.join(samples)+'</div><p>Цены без расходов на ввоз и доставку. Не автомобили в наличии.</p></section>',s,count=1);assert n==1;write(p,s)
    p=target/PRICE;s,n=re.subn(r'(<section id="pa-seo-price-samples">)[\s\S]*?</section>',lambda m:m.group(1)+'<h2>Цены реальных завершённых торгов</h2><table><thead><tr><th>Модель</th><th>Дата торгов</th><th>Цена в Японии</th></tr></thead><tbody>'+''.join(table)+'</tbody></table><p>Это архивная цена лота в иенах, не цена под ключ и не предложение к продаже. Для актуальной сметы используйте калькулятор.</p></section>',read(p),count=1);assert n==1;write(p,s)
    for m,rows in groups.items():
        text=read(target/HUB[m])
        assert all('/models/'+r["id"]+'.html' in text for r in rows)
    assert all('/'+HUB[market(r)] in read(target/"models"/(r["id"]+".html")) for r in items)
    print("PAPAUTO_SEO_INTENTS_OK "+json.dumps({"models":len(items),"by_market":{m:len(v) for m,v in groups.items()},"new_distinct_pages":[CAT,PRICE],"real_archive_examples":len(chosen),"gallery_unchanged":True}))
