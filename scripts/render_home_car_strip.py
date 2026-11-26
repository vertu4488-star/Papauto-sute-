"""Homepage ribbon of existing approved archive lots, no new media or offers."""
from pathlib import Path
from html import escape
import json
import re

from verify_publication_approval import _valid_media

PREFERRED = (
    "honda fit", "toyota aqua", "nissan note", "honda freed",
    "toyota yaris", "toyota prius", "honda vezel", "toyota corolla",
    "suzuki swift", "toyota raize", "nissan serena", "honda stepwgn",
    "mazda cx-5", "subaru forester", "toyota noah", "suzuki solio",
)

def render_home_car_strip(target: Path, registry: dict):
    def normalized(s):
        return re.sub(r"\s+", " ", str(s).casefold()).strip()

    # Only reuse the immutable public registry, never fetch photos or new lots.
    candidates = []
    for row in registry["lots"]:
        if row.get("market") != "japan" or row.get("export_restricted") or row.get("origin") != "owner_selection":
            continue
        if row.get("status") != "reference_only" or not row.get("photos") or not row.get("inspection_image"):
            continue
        if row.get("currency") != "JPY" or type(row.get("price_amount")) is not int or row["price_amount"] <= 0:
            continue
        ident = row.get("id", "")
        if not re.fullmatch(r"[a-z0-9-]+", ident) or not (target / "lots" / (ident+".html")).is_file():
            raise RuntimeError("HOME_CARS missing lot detail "+ident)
        candidates.append(row)
    candidates.sort(key=lambda x: (str(x.get("auction_date","")), int(x.get("year",0))), reverse=True)
    chosen, seen = [], set()
    for model in PREFERRED:
        hit = next((r for r in candidates if normalized(r["model"]) == model or normalized(r["model"]).startswith(model+" ")), None)
        if hit and hit["id"] not in seen:
            chosen.append(hit)
            seen.add(hit["id"])
    names = {normalized(r["model"]) for r in chosen}
    for row in candidates:
        if len(chosen) >= 16:
            break
        if row["id"] not in seen and normalized(row["model"]) not in names:
            chosen.append(row)
            seen.add(row["id"])
            names.add(normalized(row["model"]))
    if len(chosen) != 16:
        raise RuntimeError("HOME_CARS expected sixteen distinct approved examples")

    cards = []
    for i, row in enumerate(chosen):
        src = row["photos"][0]
        _valid_media(target, src)
        _valid_media(target, row["inspection_image"])
        model = escape(row["model"], quote=True)
        year = int(row["year"])
        mileage = f"{int(row['mileage_km']):,}".replace(",", " ")
        amount = f"{int(row['price_amount']):,}".replace(",", " ")
        ident = escape(row["id"], quote=True)
        cards.append(
            f'<a class="pa-home-car" href="/lots/{ident}.html" aria-label="{model}, {year}, архивный аукционный пример">'
            f'<span class="pa-home-car-media"><img src="{escape(src, quote=True)}" alt="{model}, {year}, фото конкретного лота" loading="lazy" decoding="async" width="320" height="180"></span>'
            f'<span class="pa-home-car-name">{model}, {year}</span>'
            f'<span class="pa-home-car-price">{amount} ¥</span>'
            f'<span class="pa-home-car-meta">{mileage} км · оценка {escape(str(row["grade"]))}</span>'
            '</a>')
    strip = (
        '<section id="pa-home-cars" aria-labelledby="pa-home-cars-heading">'
        '<div class="pa-home-cars-head"><h2 id="pa-home-cars-heading">Автомобили из Японии</h2>'
        '<a href="/gallery.html">Все автомобили →</a></div>'
        '<p class="pa-home-cars-note">Статистика продаж</p>'
        '<div class="pa-home-cars-shell">'
        '<button class="pa-home-cars-arrow pa-home-cars-prev" type="button" aria-label="Предыдущие автомобили" aria-controls="pa-home-cars-track" hidden>‹</button>'
        '<div id="pa-home-cars-track" class="pa-home-cars-track" tabindex="0" aria-label="Лента автомобилей, прокручивается влево и вправо">'
        + "".join(cards) +
        '</div><button class="pa-home-cars-arrow pa-home-cars-next" type="button" aria-label="Следующие автомобили" aria-controls="pa-home-cars-track" hidden>›</button></div></section>'
    )
    page = target/"index.html"
    html = page.read_text(encoding="utf-8")
    hero = '<section class="hero wrap pa-thursday-hero pa-approved-photo-hero"'
    if html.count(hero) != 1 or 'id="pa-home-cars"' in html:
        raise RuntimeError("HOME_CARS homepage hero anchor mismatch")
    html = html.replace(hero, strip + "\n" + hero, 1)
    html = html.replace("</head>", '<link rel="stylesheet" href="/papauto-home-cars.css?v=20261126"></head>', 1)
    html = html.replace("</body>", '<script defer src="/papauto-home-cars.js?v=20261126"></script></body>', 1)
    if html.count('class="pa-home-car"') != 16:
        raise RuntimeError("HOME_CARS count mismatch")
    page.write_text(html, encoding="utf-8")
    print("PAPAUTO_HOME_CARS_OK "+json.dumps({"cards":len(chosen),"new_media":0,"hero_unchanged":True,"ids":[r["id"] for r in chosen]}))
