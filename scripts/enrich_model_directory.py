"""Reuse only screened, generated model examples; keep every model URL."""
from pathlib import Path
from html import escape, unescape
import json
import re

def e(value):
    return escape(str(value), quote=True)

COUNTRY = {"japan": "Япония", "korea": "Южная Корея", "south-korea": "Южная Корея", "china": "Китай"}
ARTICLE = re.compile(r'<article class="pa-model-lot(?: pa-model-supplier)?"[^>]*>[\s\S]*?</article>')
IMAGE = re.compile(r'<img\b[^>]*\bsrc="([^"]+)"[^>]*>')
STYLE = """<style>
.pa-directory-controls{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0;align-items:end}
.pa-directory-controls label{flex:1 1 200px;font-size:13px}.pa-directory-controls input,.pa-directory-controls select{width:100%;padding:11px;border:1px solid #cdbdad;border-radius:9px;background:#fff;color:#302923;font:inherit;box-sizing:border-box}
.pa-directory-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,245px),1fr));gap:15px}
.pa-directory-card{border:1px solid #e4d8cd;background:#fff;border-radius:15px;overflow:hidden;display:flex;flex-direction:column;min-width:0}
.pa-directory-card img{width:100%;height:190px;object-fit:contain;display:block;background:#f5f1eb;border-radius:0}
.pa-directory-copy{padding:15px;display:flex;flex-direction:column;gap:6px}.pa-directory-copy h3{font-size:21px;margin:0;line-height:1.25}.pa-directory-copy p{margin:0;font-size:14px;color:#5c5148}
.pa-directory-copy .pa-directory-button{background:#754c36;color:#fff!important;padding:10px 14px;border-radius:24px;text-decoration:none;font-size:14px;display:inline-block;margin-top:6px;text-align:center}
.pa-directory-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr));gap:0 20px;list-style:none;padding:0;margin:12px 0}
.pa-directory-list li{border-bottom:1px solid #e4d8cd;padding:10px 0}.pa-directory-list a{font-weight:600}.pa-directory-list small{display:block;color:#6f6258;font-size:13px}
[data-pa-directory-entry][hidden],.pa-directory-market[hidden]{display:none!important}
.pa-model-cover{margin:18px 0;border:1px solid #e4d8cd;border-radius:17px;background:#fff;padding:12px}.pa-model-cover img{display:block;width:100%;height:clamp(210px,42vw,440px);object-fit:contain;border-radius:10px;background:#f5f1eb}.pa-model-cover figcaption{padding:8px 4px;color:#5c5148}.pa-model-cover a{display:inline-block;margin-top:5px}
</style>"""

def cover_from_page(target, html):
    cards = ARTICLE.findall(html)
    # Prioritize exact examples; related examples retain their original model name.
    cards.sort(key=lambda card: 'data-model-related-' in card)
    if not cards:
        return None
    card = cards[0]
    im = IMAGE.search(card)
    title = re.search(r'<h3>([\s\S]*?)</h3>', card)
    if not im or not title:
        raise RuntimeError("MODEL_DIRECTORY missing first approved card photo or title")
    src = unescape(im.group(1))
    if not src.startswith("/assets/") or ".." in src:
        raise RuntimeError("MODEL_DIRECTORY invalid image path")
    path = target / src.lstrip("/")
    if not path.is_file() or path.stat().st_size < 100 or path.is_symlink():
        raise RuntimeError("MODEL_DIRECTORY missing image " + src)
    name = unescape(re.sub(r'<[^>]+>', '', title.group(1))).strip()
    kind = ("Родственное семейство — " if 'data-model-related-' in card else "") + ("пример поставщика" if "pa-model-supplier" in card else "архивный аукционный пример")
    return {"src":src,"title":name,"kind":kind,"related":'data-model-related-' in card}

def render_directory(target: Path, coverage: dict):
    items = json.loads((target/"data/papauto-expanded-45x3-2026.json").read_text(encoding="utf-8"))["items"]
    report = {r["model_id"]:r for r in coverage["models"]}
    if len(items)!=135 or len(report)!=135:
        raise RuntimeError("MODEL_DIRECTORY expected 135 entries")
    covers = {}
    for item in items:
        ident = item["id"]
        page = target/"models"/(ident+".html")
        html = page.read_text(encoding="utf-8")
        cover = cover_from_page(target, html)
        expected = any(report[ident].get(k,0) for k in ("auction_matches","supplier_matches","related_cards"))
        if bool(cover) != bool(expected):
            raise RuntimeError("MODEL_DIRECTORY coverage mismatch "+ident)
        if cover:
            covers[ident] = cover
            note = cover["kind"] + " · " + cover["title"] + ". Не автомобиль в наличии."
            figure = ('<figure class="pa-model-cover"><img src="'+e(cover["src"])+'" alt="'+e(cover["title"]+" — "+cover["kind"])+'" decoding="async" fetchpriority="high"><figcaption>'+e(note)+' <a href="#pa-model-statistics">Фотографии, параметры и документы ↓</a></figcaption></figure>')
            html,count = re.subn(r'</h1>',lambda m:m.group(0)+figure,html,count=1,flags=re.I)
            if count != 1: raise RuntimeError("MODEL_DIRECTORY missing model H1 "+ident)
            html = html.replace("</head>",STYLE+"</head>",1)
            page.write_text(html,encoding="utf-8")
    sections = []
    for market in ("japan","korea","china"):
        members = [i for i in items if ("korea" if i["market"]=="south-korea" else i["market"])==market]
        cards,links = [],[]
        for item in members:
            ident = item["id"]
            name = item["brand"]+" "+item["model"]
            engine = item.get("engine") or "Уточняется по документам"
            href = "/models/"+ident+".html"
            attrs = 'id="'+e(ident)+'" data-pa-directory-entry data-name="'+e(name)+'"'
            if ident in covers:
                photo = covers[ident]
                label = photo["kind"] + " · " + photo["title"]
                cards.append('<article class="pa-directory-card" '+attrs+'><a href="'+href+'"><img src="'+e(photo["src"])+'" alt="'+e(label)+'" loading="lazy" decoding="async"></a><div class="pa-directory-copy"><h3><a href="'+href+'">'+e(name)+'</a></h3><p>'+e(COUNTRY[market])+' · '+e(engine)+'</p><p>'+e(label)+'</p><a class="pa-directory-button" href="'+href+'">Подробнее о модели →</a></div></article>')
            else:
                links.append('<li '+attrs+'><a href="'+href+'">'+e(name)+'</a><small>'+e(engine)+' · фото пока не подтверждено</small></li>')
        sections.append('<section class="pa-directory-market" data-market="'+market+'" id="'+market+'"><h2>'+COUNTRY[market]+'</h2><div class="pa-directory-grid">'+"".join(cards)+'</div>'+('<h3>Другие модели — справочник</h3><ul class="pa-directory-list">'+"".join(links)+'</ul>' if links else '')+'</section>')
    hub = target/"models-135.html"
    html = hub.read_text(encoding="utf-8")
    main = ('<main><h1>135 моделей автомобилей под заказ</h1><p>Япония, Южная Корея и Китай. Выберите модель, чтобы посмотреть характеристики, документы и примеры подбора. Фото показываем только при наличии подтверждённых материалов.</p>'
            '<nav class="nav"><a href="#japan">Япония</a><a href="#korea">Корея</a><a href="#china">Китай</a><a href="/?view=calculator">Калькулятор</a></nav>'
            '<div class="pa-directory-controls" hidden><label>Поиск модели<input id="pa-directory-search" type="search" placeholder="Honda Fit, Toyota Prius…"></label><label>Рынок<select id="pa-directory-market"><option value="">Все страны</option><option value="japan">Япония</option><option value="korea">Южная Корея</option><option value="china">Китай</option></select></label></div><p id="pa-directory-count" role="status">135 моделей</p>'
            +"".join(sections)+'</main>')
    html,count = re.subn(r'<main>[\s\S]*?</main>',lambda _:main,html,count=1)
    if count!=1: raise RuntimeError("MODEL_DIRECTORY main not found")
    html=html.replace("</head>",STYLE+'<script defer src="/model-directory.js?v=20261126"></script></head>',1)
    if len(re.findall(r'data-pa-directory-entry\b',html))!=135 or len(re.findall(r'<article class="pa-directory-card"',html))!=len(covers):
        raise RuntimeError("MODEL_DIRECTORY card count mismatch")
    hub.write_text(html,encoding="utf-8")
    # Legacy address stays usable; identical content has one canonical directory.
    (target/"models-100.html").write_text(html,encoding="utf-8")
    print("PAPAUTO_MODEL_DIRECTORY_OK "+json.dumps({"pages":135,"photo_cards":len(covers),"text_links":135-len(covers),"legacy_alias":True},ensure_ascii=False))
