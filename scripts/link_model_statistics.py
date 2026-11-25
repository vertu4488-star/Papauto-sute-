"""Render model-specific examples from the already screened public registry.
No new lot, photo, sale evidence, or provider inventory is created here.
Supplier offers are kept in their dedicated China section, not relabelled as auctions.
"""
from collections import defaultdict, Counter
from html import escape, unescape
from pathlib import Path
from urllib.parse import quote
import json
import re

MEDIA = re.compile(r"/assets/(?:auction/(?:home|approved)|premium-auctions)/[a-zA-Z0-9._-]+\.(?:jpg|jpeg|png|webp)", re.I)
SUPPLIER = re.compile(r"/assets/china-order/[a-zA-Z0-9/_-]+\.jpg", re.I)
SLUG = re.compile(r"[a-z0-9-]+")
MARKET = {"japan": "japan", "korea": "korea", "south-korea": "korea", "china": "china"}
CURRENCY = {"japan": "JPY", "korea": "KRW", "china": "CNY"}
FORBIDDEN = {"nissan-note-2021-227", "mercedes-a180-2020"}
MAX_CARDS = 10

# Exact aliases only; never match arbitrary substrings (Yaris != Yaris Cross,
# Corolla != Axio/Fielder, Note != Roox, Song Plus != Song Pro).
# Specific variants retain their original full model name on the card.
ALIASES = {
    "japan": {
        "Toyota Corolla Sport": "japan-toyota-corolla",
        "Toyota Corolla Touring": "japan-toyota-corolla",
        "Suzuki Jimny Sierra": "japan-suzuki-jimny",
        "Honda Freed Spike": "japan-honda-freed",
        "Honda Freed+": "japan-honda-freed",
        "Mazda Mazda2": "japan-mazda-demio",
        "Toyota Prius PHV": "japan-toyota-prius",
        "Toyota Prius PHEV": "japan-toyota-prius",
        "Nissan Note e-POWER": "japan-nissan-note-e-power",
    },
    "china": {
        "Geely Binyue": "china-geely-coolray-binyue",
        "Geely Coolray": "china-geely-coolray-binyue",
        "Geely Boyue": "china-geely-atlas-boyue",
        "Geely Atlas": "china-geely-atlas-boyue",
        "Geely Xingyue L": "china-geely-monjaro",
        "Geely Boyue Cool": "china-geely-cityray",
        "BYD Yuan Plus": "china-byd-yuan-plus-atto-3",
        "BYD Atto 3": "china-byd-yuan-plus-atto-3",
        "BYD Qin Plus DM-i": "china-byd-qin-plus",
        "BYD Qin Plus EV": "china-byd-qin-plus",
        "BYD Qin L DM-i": "china-byd-qin-l",
        "BYD Qin L EV": "china-byd-qin-l",
        "BYD Seal 06 DM-i": "china-byd-seal-06",
        "BYD Song L DM-i": "china-byd-song-l",
        "BYD Song L EV": "china-byd-song-l",
        "BYD Song Plus DM-i": "china-byd-song-plus",
        "BYD Song Plus EV": "china-byd-song-plus",
        "BYD Song Pro DM-i": "china-byd-song-pro",
        "Haval Dargo": "china-haval-big-dog-dargo",
        "Haval Big Dog": "china-haval-big-dog-dargo",
        "Haval Dargo Plus": "china-haval-big-dog-dargo",
        "Jetour X70": "china-chery-jetour-x70",
        "Jetour X70 Plus": "china-chery-jetour-x70",
        "Omoda 5": "china-chery-omoda-5",
        "GAC Trumpchi GS3": "china-gac-gs3",
        "GAC Trumpchi GS3 Emzoom": "china-gac-gs3",
        "Aion Y": "china-gac-aion-y",
        "Aion Y Plus": "china-gac-aion-y",
    },
    "korea": {
        "Hyundai Avante": "korea-hyundai-avante-elantra",
        "Hyundai Elantra": "korea-hyundai-avante-elantra",
        "Kia K3": "korea-kia-k3-cerato",
        "Kia Cerato": "korea-kia-k3-cerato",
        "Kia Morning": "korea-kia-morning-picanto",
        "Kia Picanto": "korea-kia-morning-picanto",
        "Chevrolet Trax": "korea-chevrolet-korea-trax",
        "Chevrolet Trax Crossover": "korea-chevrolet-korea-trax",
        "Renault Korea XM3": "korea-renault-korea-xm3-arkana",
        "Renault Korea Arkana": "korea-renault-korea-xm3-arkana",
        "Renault Samsung SM3": "korea-renault-korea-sm3",
        "KGM Korando": "korea-ssangyong-korando",
        "KGM Tivoli": "korea-ssangyong-tivoli",
    },
}
RELATED_ONLY = {
    "japan-honda-jazz": "japan-honda-fit",
    "japan-nissan-micra": "japan-nissan-march",
    "japan-nissan-qashqai": "japan-nissan-juke",
    "korea-kia-forte": "korea-kia-k3-cerato",
    "korea-hyundai-creta": "korea-hyundai-kona",
    "korea-hyundai-bayon": "korea-hyundai-venue",
    "korea-kia-kx3": "korea-kia-seltos",
    "china-chery-tiggo-4": "china-chery-tiggo-5x",
}

def esc(value):
    return escape(str(value), quote=True)

def norm(value):
    # Keep "+" meaningful (Freed+ and Song Plus are not arbitrary prefixes).
    return re.sub(r"[\s\-_]+", "", unescape(str(value)).casefold())

def money(value):
    return f"{int(value):,}".replace(",", " ")

def make_index(items):
    index = {}
    for item in items:
        market = MARKET[item["market"]]
        ident = item["id"]
        key = (market, norm(item["brand"] + " " + item["model"]))
        if key in index:
            raise RuntimeError("MODEL_STATS duplicate reference " + ident)
        index[key] = ident
    valid = {x["id"] for x in items}
    for market, aliases in ALIASES.items():
        for name, ident in aliases.items():
            if ident not in valid:
                raise RuntimeError("MODEL_STATS unknown alias " + ident)
            key = (market, norm(name))
            if key in index and index[key] != ident:
                raise RuntimeError("MODEL_STATS ambiguous alias " + name)
            index[key] = ident
    return index

def match(index, market, name, body=""):
    market = MARKET.get(market)
    if not market:
        return None
    # E13/NE13 are e-POWER in the Japanese Note family. Do not infer E12
    # hybrid status from the name alone; leave source label unchanged.
    if market == "japan" and norm(name) == norm("Nissan Note"):
        if re.fullmatch(r"(?:[A-Z0-9]+-)?(?:E13|NE13|SNE13|HE12|SHE12)", str(body).upper().strip()):
            return "japan-nissan-note-e-power"
    return index.get((market, norm(name)))

def assert_media(target, path, pattern):
    if not isinstance(path, str) or not pattern.fullmatch(path):
        raise RuntimeError("MODEL_STATS non-approved asset path")
    file = target / path.lstrip("/")
    if file.is_symlink() or not file.is_file() or file.stat().st_size < 100:
        raise RuntimeError("MODEL_STATS missing or invalid asset " + path)

def lot_card(row, target):
    ident = row["id"]
    if not SLUG.fullmatch(ident) or ident in FORBIDDEN:
        raise RuntimeError("MODEL_STATS rejected lot")
    photos = row.get("photos") or []
    sheet = row.get("inspection_image")
    if not photos or row.get("inspection_kind") != "Аукционный лист" or sheet in photos:
        raise RuntimeError("MODEL_STATS missing original photo/sheet " + ident)
    for asset in [photos[0], sheet]:
        assert_media(target, asset, MEDIA)
    detail = "/lots/" + ident + ".html"
    if not (target / detail.lstrip("/")).is_file():
        raise RuntimeError("MODEL_STATS no lot detail " + ident)
    name = row["model"]
    label = str(row.get("sale_label") or "Цена продажи не подтверждена")
    amount = row.get("price_amount", row.get("price_jpy", 0))
    currency = row.get("currency") or CURRENCY[MARKET[row["market"]]]
    price = money(amount) + " " + currency if type(amount) in (int, float) and amount > 0 else "Не подтверждена"
    note = "Завершённые торги" if row.get("status") == "sold" else "Архивный пример, не подтверждённая продажа"
    fields = [
        ("Пробег", money(row["mileage_km"]) + " км"), ("Оценка", row.get("grade") or "Не указана"),
        ("Кузов", row.get("body") or "Не указан"), ("Торги", row.get("auction") or "Не указаны"),
        ("Дата", row.get("auction_date") or "Не указана"),
    ]
    if row.get("trim"):
        fields.append(("Комплектация", row["trim"]))
    if row.get("engine_cc"):
        fields.append(("Двигатель", str(row["engine_cc"]) + " см³"))
    if row.get("power_hp"):
        fields.append(("Мощность", str(row["power_hp"]) + " л. с."))
    facts = "".join("<div><dt>"+esc(k)+"</dt><dd>"+esc(v)+"</dd></div>" for k,v in fields)
    estimate = "/?view=calculator&market=" + quote(row["market"],safe="") + "&vehicle=" + quote("lot:"+ident,safe="")
    return (
        '<article class="pa-model-lot" data-model-lot-id="'+esc(ident)+'">'
        '<a href="'+esc(detail)+'"><img loading="lazy" decoding="async" src="'+esc(photos[0])+
        '" alt="'+esc(name+" "+str(row["year"])+" — оригинальное фото лота")+'"></a>'
        '<div class="pa-model-lot-body"><h3><a href="'+esc(detail)+'">'+esc(name)+" · "+esc(row["year"])+'</a></h3>'
        '<p class="pa-model-lot-note">'+esc(note)+'</p><dl>'+facts+'</dl>'
        '<p>'+esc(row.get("description") or "")+'</p><p><strong>'+esc(label)+': '+esc(price)+'</strong>'
        ' — без таможни и доставки.</p><div class="pa-model-lot-actions">'
        '<a href="'+esc(detail)+'">Все фото и подробности</a><a href="'+esc(sheet)+'">Аукционный лист</a>'
        '<a href="'+esc(estimate)+'">Рассчитать стоимость</a></div></div></article>'
    )

STYLE = """<style>
#pa-model-statistics{margin:20px 0;padding:clamp(14px,3vw,22px);background:#fff;border-radius:20px}
#pa-model-statistics .pa-model-lot-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,270px),1fr));gap:16px}
#pa-model-statistics .pa-model-lot{min-width:0;border:1px solid #e9e2d8;border-radius:14px;overflow:hidden;background:#fff}
#pa-model-statistics .pa-model-lot img{display:block;width:100%;height:200px;object-fit:contain;background:#f7f5f1}
#pa-model-statistics .pa-model-lot-body{padding:14px;overflow-wrap:anywhere}
#pa-model-statistics .pa-model-lot h3{font-size:18px;line-height:1.3;margin:0 0 8px}
#pa-model-statistics .pa-model-lot dl{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:12px 0}
#pa-model-statistics .pa-model-lot dt{font-size:13px;color:#625c53}
#pa-model-statistics .pa-model-lot dd{margin:0;font-weight:500}
#pa-model-statistics .pa-model-lot-note{font-size:14px;color:#625c53}
#pa-model-statistics .pa-model-lot-actions{display:flex;flex-wrap:wrap;gap:10px 14px}
#pa-model-statistics .pa-model-lot-actions a{font-size:14px}
#pa-model-statistics details{margin:14px 0}#pa-model-statistics li{margin:6px 0}
.cn-example[id]{scroll-margin-top:100px}
</style>"""

def supplier_links(target, approved_paths, index):
    """Link to existing screened supplier cards; no supplier images are copied."""
    page = target / "china-order.html"
    html = page.read_text(encoding="utf-8")
    linked = defaultdict(list)
    seen = set()
    def mark(hit):
        card = hit.group(0)
        src = re.search(r'<img\b[^>]*\bsrc="([^"]+)"', card)
        title = re.search(r'<h2>([^<]+)</h2>', card)
        if not src or not title:
            raise RuntimeError("MODEL_STATS supplier card missing photo or title")
        path = src.group(1)
        if path.lstrip("/") not in approved_paths:
            raise RuntimeError("MODEL_STATS supplier outside approved set")
        assert_media(target, path, SUPPLIER)
        if path in seen:
            raise RuntimeError("MODEL_STATS duplicate supplier photo")
        seen.add(path)
        anchor = "supplier-" + Path(path).parent.name + "-" + Path(path).stem
        if not SLUG.fullmatch(anchor):
            raise RuntimeError("MODEL_STATS bad supplier anchor")
        title = unescape(title.group(1)).strip()
        # Strip a year at either edge, never strip arbitrary model suffixes.
        name = re.sub(r"^\s*(?:19|20)\d{2}\s+|\s+(?:19|20)\d{2}\s*$", "", title).strip()
        ident = match(index, "china", name)
        if ident:
            linked[ident].append((title, anchor))
        return card.replace('<article class="cn-example"', '<article class="cn-example" id="'+anchor+'"', 1)
    html = re.sub(r'<article class="cn-example"[^>]*>[\s\S]*?</article>', mark, html)
    if seen != {"/"+p for p in approved_paths}:
        raise RuntimeError("MODEL_STATS supplier source mismatch")
    page.write_text(html, encoding="utf-8")
    return linked

def render(target: Path, registry: dict, approved_supplier_paths: set):
    items = json.loads((target / "data/papauto-expanded-45x3-2026.json").read_text(encoding="utf-8"))["items"]
    refs = {x["id"]: x for x in items}
    if len(items) != 135 or len(refs) != 135:
        raise RuntimeError("MODEL_STATS expected 135 model references")
    if {p.stem for p in (target/"models").glob("*.html")} != set(refs):
        raise RuntimeError("MODEL_STATS reference/page mismatch")
    index = make_index(items)
    assert match(index,"japan","Toyota Yaris Cross") == "japan-toyota-yaris-cross"
    assert match(index,"japan","Toyota Corolla Fielder") == "japan-toyota-corolla-fielder"
    assert match(index,"china","Toyota Corolla") == "china-toyota-corolla"
    assert match(index,"korea","Toyota Corolla") is None
    assert match(index,"japan","Nissan Note","E13") == "japan-nissan-note-e-power"
    assert match(index,"japan","Nissan Note","E12") == "japan-nissan-note"
    assert match(index,"china","Toyota Corolla Cross") is None
    assert match(index,"china","BYD Song MAX") is None
    grouped = defaultdict(list)
    assigned = {}
    for row in registry["lots"]:
        if row["id"] in FORBIDDEN:
            raise RuntimeError("MODEL_STATS withdrawn lot")
        ident = match(index, row["market"], row["model"], row.get("body",""))
        if ident:
            if row["id"] in assigned:
                raise RuntimeError("MODEL_STATS lot duplicated")
            assigned[row["id"]] = ident
            grouped[ident].append(row)
    supplier = supplier_links(target, approved_supplier_paths, index)
    report = []
    for ident, item in refs.items():
        page = target/"models"/(ident+".html")
        html = page.read_text(encoding="utf-8")
        records = sorted(grouped[ident], key=lambda x:(str(x.get("auction_date") or ""),x["year"],x["id"]), reverse=True)
        name = item["brand"]+" "+item["model"]
        parts = ['<section id="pa-model-statistics" aria-label="Аукционная статистика модели"><h2>Аукционная статистика: '+esc(name)+'</h2>']
        if records:
            parts += ['<p>В нашей базе: '+str(len(records))+' документированных аукционных примеров по этой модели и стране. Архивные цены не являются текущими предложениями или стоимостью под ключ. Проверка доступности ввоза обязательна.</p><div class="pa-model-lot-grid">']
            parts += [lot_card(row,target) for row in records[:MAX_CARDS]]
            parts += ['</div>']
            if len(records)>MAX_CARDS:
                parts += ['<details><summary>Остальные примеры ('+str(len(records)-MAX_CARDS)+')</summary><ul>']
                for row in records[MAX_CARDS:]:
                    # Validate remaining records as well, even when only linked.
                    lot_card(row,target)
                    parts += ['<li><a href="/lots/'+esc(row["id"])+'.html">'+esc(row["model"])+' · '+esc(row["year"])+' · '+money(row["mileage_km"])+' км · '+esc(row.get("auction_date",""))+'</a></li>']
                parts += ['</ul></details>']
        else:
            parts += ['<p>В опубликованной базе пока нет подходящего аукционного примера этой модели из выбранной страны с оригинальным фото и полным аукционным листом. Не подставляем фото другой модели или страны.</p>']
        offers = supplier[ident]
        if offers:
            parts += ['<h3>Примеры поставщиков из Китая ('+str(len(offers))+')</h3><p>Это отдельный каталог подбора, не статистика завершённых торгов. Аукционные листы для этих предложений не подтверждены; фотографии, пробег и цена FOB доступны в соответствующих карточках поставщиков.</p><ul>']
            for title, anchor in offers[:MAX_CARDS]:
                parts += ['<li><a href="/china-order.html#'+esc(anchor)+'">'+esc(title)+' — фото и параметры в каталоге поставщика</a></li>']
            parts += ['</ul>']
            if len(offers)>MAX_CARDS:
                parts += ['<details><summary>Ещё '+str(len(offers)-MAX_CARDS)+' примеров поставщиков</summary><ul>']
                for title,anchor in offers[MAX_CARDS:]:
                    parts += ['<li><a href="/china-order.html#'+esc(anchor)+'">'+esc(title)+'</a></li>']
                parts += ['</ul></details>']
        if not records and ident in RELATED_ONLY:
            other=RELATED_ONLY[ident]
            if other not in refs:
                raise RuntimeError("MODEL_STATS unknown related page")
            parts += ['<p>Отдельно можно <a href="/models/'+esc(other)+'.html">посмотреть родственную модель</a>; её автомобили не считаются примерами этой страницы.</p>']
        parts += ['<p><a href="/gallery.html">Вся аукционная статистика</a> · <a href="/podbor.html?similar='+esc(quote(name+" · "+item["market"],safe=""))+'">Запросить подбор этой модели</a></p></section>']
        pattern = r'<section><h2>Фото, пробег и документы</h2>[\s\S]*?</section>'
        html, count = re.subn(pattern,lambda _: "".join(parts),html,count=1)
        if count!=1 or html.count('id="pa-model-statistics"')!=1:
            raise RuntimeError("MODEL_STATS missing or duplicate photo section "+ident)
        html = html.replace("</head>",STYLE+"</head>",1)
        page.write_text(html, encoding="utf-8")
        report.append({"model_id":ident,"market":item["market"],"auction_matches":len(records),"auction_cards":min(len(records),MAX_CARDS),"supplier_matches":len(offers)})
    # Reverse navigation: only exact approved assigned lots point to model pages.
    for lot_id, ident in assigned.items():
        p=target/"lots"/(lot_id+".html")
        html=p.read_text(encoding="utf-8")
        label=refs[ident]["brand"]+" "+refs[ident]["model"]
        link='<p class="pa-model-back"><a href="/models/'+esc(ident)+'.html">Все примеры и описание '+esc(label)+'</a></p>'
        html,count=re.subn(r"</main>",lambda _:link+"</main>",html,count=1,flags=re.I)
        if count!=1: raise RuntimeError("MODEL_STATS no main in lot "+lot_id)
        p.write_text(html,encoding="utf-8")
    # Remove legacy gallery figures from the hub if they refer to a withdrawn
    # or unassigned model; the generated model page is the authoritative view.
    hub=target/"models-135.html"
    html=hub.read_text(encoding="utf-8")
    def scrub(hit):
        card=hit.group(0)
        ident=hit.group(1)
        allowed={(r["photos"][0],r["inspection_image"]) for r in grouped[ident]}
        def figure(f):
            src=re.search(r'<img\b[^>]*\bsrc="([^"]+)"',f.group(0))
            return f.group(0) if src and any(src.group(1)==p and s in f.group(0) for p,s in allowed) else ""
        return re.sub(r"<figure>[\s\S]*?</figure>",figure,card)
    html=re.sub(r'<article id="([a-z0-9-]+)" class="model">[\s\S]*?</article>',scrub,html)
    hub.write_text(html,encoding="utf-8")
    summary={"model_pages":len(report),"auction_covered":sum(x["auction_matches"]>0 for x in report),
             "auction_matches":len(assigned),"auction_cards":sum(x["auction_cards"] for x in report),
             "supplier_covered":sum(x["supplier_matches"]>0 for x in report),
             "supplier_matches":sum(x["supplier_matches"] for x in report),
             "no_exact_examples":sum(x["auction_matches"]==0 and x["supplier_matches"]==0 for x in report),
             "models":report}
    (target/"data/model-statistics-coverage.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PAPAUTO_MODEL_STATS_OK "+json.dumps({k:v for k,v in summary.items() if k!="models"},ensure_ascii=False))
    return summary
