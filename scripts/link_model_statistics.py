"""Render model-specific examples from the already screened public registry.
No new lot, photo, sale evidence, or provider inventory is created here.
Supplier offers reuse the exact screened China catalogue records on model pages,
never relabelled as auctions; no files or prices are duplicated in the source data.
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
# Reviewed full titles from the existing owner-approved China catalogue.
SUPPLIER_TITLE_ALIASES = {
    "Chery · Tiggo 7 2024 1.5T CVT Luxury Edition · 2024": "china-chery-tiggo-7",
    "Chery · Tiggo 7 2024 Super Power Edition 1.5T CVT Super Power Luxury · 2024": "china-chery-tiggo-7",
    "Chery · Arrizo 5 2021 PRO 1.5L CVT Youth Edition · 2022": "china-chery-arrizo-5",
    "Mazda CX-30 2022 ed. · 2022": "china-mazda-cx-30",
    "Chery Omoda 5 2022 ed. · 2022": "china-chery-omoda-5",
    "Haval Jolion Pro 2022 ed. · 2022": "china-haval-jolion",
    "Toyota Corolla 2021 ed. · 2022": "china-toyota-corolla",
    "Jetour X70 PLUS 2021 ed. · 2022": "china-chery-jetour-x70",
    "Volkswagen Lavida 2023 ed. · 2022": "china-volkswagen-lavida",
    "Haval H6 Series 2023 ed. · 2023": "china-haval-h6",
    "Haval Dargo 2022 ed. · 2022": "china-haval-big-dog-dargo",
    "Volkswagen Lavida 280TSI DSG Comfort · 2021": "china-volkswagen-lavida",
    "Chery Tiggo 5x 2022 ed. · 2023": "china-chery-tiggo-5x",
    "Toyota Corolla 2021 ed. · 2023": "china-toyota-corolla",
    "Haval H6 Series 2023 ed. · 2022": "china-haval-h6",
    "2017 Geely Emgrand Sedan Million Edition 1.5L CVT Luxury Edition": "china-geely-emgrand",
    "2023 Jetour X70 1.5T DCT Beyond PRO Edition 7-Seater": "china-chery-jetour-x70",
    "2021 Changan Eado PLUS 1.6L GDI CVT Elite Edition": "china-changan-eado",
    "2022 Changan UNI-T 1.5T Intelligent Navigator Edition": "china-changan-uni-t",
    "2021 Haval H6 1.5GDIT Automatic Luxury Edition": "china-haval-h6",
    "2024 Geely Binrui COOL 1.5T DCT Champion Edition": "china-geely-binrui",
    "2019 Haval H6 Sport Edition 1.5T Automatic 2WD Elite Edition China VI": "china-haval-h6",
    "2017 Haval H6 Blue Label Sport Edition 1.5T Automatic 2WD Exclusive Edition": "china-haval-h6",
    "2019 Geely Emgrand Lingjun Edition 1.5L CVT Luxury Edition China VI": "china-geely-emgrand",
    "2017 Volkswagen Lavida 1.6L Manual Fashion Edition": "china-volkswagen-lavida",
    "2022 Geely Binyue PHEV": "china-geely-coolray-binyue"
}

RELATED_ONLY = {
    "japan-honda-jazz": "japan-honda-fit",
    "japan-nissan-micra": "japan-nissan-march",
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
    """Read exact approved supplier records; reuse local assets, never copy bytes."""
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
        ident = match(index, "china", name) or SUPPLIER_TITLE_ALIASES.get(title)
        if ident:
            if not re.search(r"\b(?:19|20)\d{2}\b", title):
                raise RuntimeError("MODEL_STATS missing supplier year "+anchor)
            fields = [(unescape(k).strip(), unescape(v).strip()) for k,v in
                      re.findall(r"<dt>([^<]+)</dt>\s*<dd>([^<]+)</dd>", card)]
            descriptions = re.findall(r"<p>([^<]+)</p>", card)
            if (not fields or any(not k or not v for k,v in fields)
                    or not any(k == "Двигатель" for k,v in fields)
                    or not any("Пробег" in k and re.search(r"\d",v) for k,v in fields)
                    or not any(("FOB" in k or "цена" in k.casefold()) and re.search(r"\d",v) for k,v in fields)
                    or not descriptions):
                raise RuntimeError("MODEL_STATS incomplete supplier data "+anchor)
            linked[ident].append({"title":title,"anchor":anchor,"photo":path,
                                  "fields":fields,"description":" ".join(unescape(x).strip() for x in descriptions)})
        return card.replace('<article class="cn-example"', '<article class="cn-example" id="'+anchor+'"', 1)
    html = re.sub(r'<article class="cn-example"[^>]*>[\s\S]*?</article>', mark, html)
    if seen != {"/"+p for p in approved_paths}:
        raise RuntimeError("MODEL_STATS supplier source mismatch")
    page.write_text(html, encoding="utf-8")
    return linked

def supplier_card(row, target, approved_paths):
    """Display source fields verbatim; never invent a sale price or auction sheet."""
    photo = row["photo"]
    anchor = row["anchor"]
    title = row["title"]
    if photo.lstrip("/") not in approved_paths or not SLUG.fullmatch(anchor):
        raise RuntimeError("MODEL_STATS unapproved supplier card")
    assert_media(target, photo, SUPPLIER)
    facts = "".join("<div><dt>"+esc(k)+"</dt><dd>"+esc(v)+"</dd></div>" for k,v in row["fields"])
    is_fob = any("FOB" in k for k,v in row["fields"])
    estimate = "/?view=calculator&market=china"
    if is_fob:
        estimate += "&vehicle="+quote("cn:"+photo,safe="")
    price_note = ("FOB — цена по данным источника, не итоговая стоимость в России." if is_fob else
                  "Цена по данным поставщика; состав и условия цены не подтверждены как FOB. Для расчёта уточните исходную цену.")
    apply = "/podbor.html?similar="+quote(title+" · КИТАЙ",safe="")
    return (
        '<article class="pa-model-lot pa-model-supplier" data-model-supplier-id="'+esc(anchor)+'">'
        '<img loading="lazy" decoding="async" src="'+esc(photo)+'" alt="'+esc(title+" — фото поставщика")+'">'
        '<div class="pa-model-lot-body"><h3>'+esc(title)+'</h3>'
        '<p class="pa-model-lot-note">Пример подбора из Китая · данные поставщика</p>'
        '<dl>'+facts+'</dl><p>'+esc(row["description"])+'</p>'
        '<p class="pa-model-lot-note">'+esc(price_note)+' '
        'Аукционный лист не подтверждён; наличие и документы уточняются до покупки.</p>'
        '<div class="pa-model-lot-actions"><a href="'+esc(estimate)+'">Рассчитать стоимость</a>'
        '<a href="'+esc(apply)+'">Подобрать аналог</a></div></div></article>'
    )

# Official manufacturer nameplate equivalences, not new auction records.
# Fit/Jazz: Honda newsroom 4070717-eng, 4101006eng.
# March/Micra: Nissan newsroom 100302-01-e (fourth generation K13).
def nameplate_examples(ident, grouped):
    if ident == "japan-honda-jazz":
        return ("Honda Fit — японское название семейства Jazz",
                "Показаны реальные японские Fit, не экспортные Jazz. Комплектации, двигатель и рынок сверяются по документам.",
                "japan-honda-fit",
                [r for r in grouped["japan-honda-fit"] if r["market"] == "japan"])
    if ident == "japan-nissan-micra":
        return ("Nissan March K13 — японский аналог Micra четвёртого поколения",
                "В карточках сохранено имя March из аукционных документов. Европейские Micra K14 и другие поколения сюда не включены.",
                "japan-nissan-march",
                [r for r in grouped["japan-nissan-march"] if r["market"] == "japan" and
                 re.fullmatch(r"(?:[A-Z0-9]+-)?(?:K13|NK13)", str(r.get("body","")).upper().strip())])
    return ("","","",[])

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
        heading = "Примеры автомобилей" if supplier[ident] and not records else "Аукционная статистика"
        parts = ['<section id="pa-model-statistics" aria-label="'+esc(heading)+'"><h2>'+esc(heading)+': '+esc(name)+'</h2>']
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
        elif not supplier[ident]:
            parts += ['<p>В опубликованной базе пока нет подходящего аукционного примера этой модели из выбранной страны с оригинальным фото и полным аукционным листом. Не подставляем фото другой модели или страны.</p>']
        offers = supplier[ident]
        if offers:
            parts += ['<h3>Автомобили из Китая: примеры подбора ('+str(len(offers))+')</h3>'
                      '<p>Фото, параметры и цены взяты из нашего утверждённого каталога поставщиков. '
                      'Это не статистика завершённых торгов; аукционные листы не подтверждены.</p>'
                      '<div class="pa-model-lot-grid">']
            parts += [supplier_card(row,target,approved_supplier_paths) for row in offers[:MAX_CARDS]]
            parts += ['</div>']
            if len(offers)>MAX_CARDS:
                parts += ['<details><summary>Ещё '+str(len(offers)-MAX_CARDS)+' примеров поставщиков</summary><div class="pa-model-lot-grid">']
                parts += [supplier_card(row,target,approved_supplier_paths) for row in offers[MAX_CARDS:]]
                parts += ['</div></details>']
        family_title, family_note, family_id, family_rows = nameplate_examples(ident, grouped)
        family_rows = sorted(family_rows, key=lambda x:(str(x.get("auction_date") or ""),x["year"],x["id"]), reverse=True)[:5] if not records else []
        if family_rows:
            parts += ['<h3>'+esc(family_title)+'</h3><p>'+esc(family_note)+'</p><div class="pa-model-lot-grid">']
            for row in family_rows:
                card = lot_card(row,target).replace('data-model-lot-id=', 'data-model-related-lot-id=',1)
                parts += [card]
            parts += ['</div><p><a href="/models/'+esc(family_id)+'.html">Все примеры японского названия модели</a></p>']
        # Chery's own 2021 release identifies Tiggo 5X (Tiggo 4 Pro).
        # Preserve exact Chinese-market source names and do not count duplicate vehicles.
        related_supplier = supplier["china-chery-tiggo-5x"][:5] if ident == "china-chery-tiggo-4" and not offers else []
        if related_supplier:
            parts += ['<h3>Chery Tiggo 5X — китайская версия семейства Tiggo 4 Pro</h3><p>По информации производителя, Tiggo 5X известен на экспортных рынках как Tiggo 4 Pro. Ниже — реальные примеры китайских 5X; комплектации и характеристики экспортной версии могут отличаться. Это не отдельные лоты Tiggo 4.</p><div class="pa-model-lot-grid">']
            parts += [supplier_card(row,target,approved_supplier_paths).replace('data-model-supplier-id=', 'data-model-related-supplier-id=',1) for row in related_supplier]
            parts += ['</div><p><a href="/models/china-chery-tiggo-5x.html">Все примеры китайских Tiggo 5X</a></p>']
        if not records and ident in RELATED_ONLY and not family_rows and not related_supplier:
            other=RELATED_ONLY[ident]
            if other not in refs:
                raise RuntimeError("MODEL_STATS unknown related page")
            parts += ['<p>Отдельно можно <a href="/models/'+esc(other)+'.html">посмотреть родственную модель</a>; её автомобили не считаются примерами этой страницы.</p>']
        if ident == "japan-nissan-qashqai":
            parts += ['<p>Только архивная справка. Прямой экспорт Dualis 2.0 из Японии в Россию ограничен; заказать или рассчитать поставку этой модели нельзя.</p></section>']
        else:
            parts += ['<p><a href="/gallery.html">Вся аукционная статистика</a> · <a href="/podbor.html?similar='+esc(quote(name+" · "+item["market"],safe=""))+'">Запросить подбор этой модели</a></p></section>']
        pattern = r'<section><h2>Фото, пробег и документы</h2>[\s\S]*?</section>'
        html, count = re.subn(pattern,lambda _: "".join(parts),html,count=1)
        if count!=1 or html.count('id="pa-model-statistics"')!=1:
            raise RuntimeError("MODEL_STATS missing or duplicate photo section "+ident)
        html = html.replace("</head>",STYLE+"</head>",1)
        # Check generated HTML against the exact source image set and unique IDs.
        supplier_ids = re.findall(r'data-model-supplier-id="([^"]+)"', html)
        supplier_photos = re.findall(r'<img\b[^>]*\bsrc="(/assets/china-order/[^"]+)"', html)
        if (supplier_ids != [row["anchor"] for row in offers]
                or supplier_photos != [row["photo"] for row in offers + related_supplier]
                or re.findall(r'data-model-related-supplier-id="([^"]+)"', html) != [row["anchor"] for row in related_supplier]
                or len(set(supplier_ids)) != len(supplier_ids)
                or any(x not in approved_supplier_paths for x in [p.lstrip("/") for p in supplier_photos])
                or ((offers or related_supplier) and item["market"] != "china")):
            raise RuntimeError("MODEL_STATS supplier render mismatch "+ident)
        page.write_text(html, encoding="utf-8")
        report.append({"model_id":ident,"market":item["market"],"auction_matches":len(records),"auction_cards":min(len(records),MAX_CARDS),"supplier_matches":len(offers),"supplier_cards":len(supplier_ids),"related_cards":len(family_rows)+len(related_supplier),"related_supplier_cards":len(related_supplier)})
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
             "supplier_cards":sum(x["supplier_cards"] for x in report),
             "related_supplier_cards":sum(x["related_supplier_cards"] for x in report),
             "no_exact_examples":sum(x["auction_matches"]==0 and x["supplier_matches"]==0 for x in report),
             "related_only_covered":sum(x["related_cards"]>0 and not x["auction_matches"] and not x["supplier_matches"] for x in report),
             "no_examples_including_related":sum(not x["auction_matches"] and not x["supplier_matches"] and not x["related_cards"] for x in report),
             "models":report}
    (target/"data/model-statistics-coverage.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PAPAUTO_MODEL_STATS_OK "+json.dumps({k:v for k,v in summary.items() if k!="models"},ensure_ascii=False))
    print("PAPAUTO_MODEL_STATS_MISSING "+json.dumps([x["model_id"] for x in report if not x["auction_matches"] and not x["supplier_matches"]],ensure_ascii=False))
    return summary
