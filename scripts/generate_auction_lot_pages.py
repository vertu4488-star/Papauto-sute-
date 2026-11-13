"""Render self-hosted, no-index full auction lot detail pages with authentic local media.

Source: the same verified full-sheet gallery registry shown to buyers. Does not
download images, fabricate models, contact sellers, or submit to search engines.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import quote

SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{2,75}$")
MEDIA = re.compile(
    r"^/assets/(?:auction/home/[a-z0-9-]+\.jpg"
    r"|premium-auctions/[a-z0-9-]+\.webp"
    r"|auction/approved/[a-z0-9-]+\.(?:jpg|jpeg|png|webp))$"
)
MARKETS = {
    "japan": ("Япония", "JPY", "¥"),
    "south-korea": ("Южная Корея", "KRW", "₩"),
    "china": ("Китай", "CNY", "¥"),
}


def safe(value: object) -> str:
    return html.escape(str(value), quote=True)


def check_media(value: object, asset_root: Path) -> str:
    if not isinstance(value, str) or not MEDIA.fullmatch(value):
        raise RuntimeError("PAPAUTO LOT: image is not an approved local auction asset: " + str(value))
    file = asset_root / value.lstrip("/")
    if file.is_symlink() or not file.is_file() or file.stat().st_size < 100:
        raise RuntimeError("PAPAUTO LOT: missing original auction photo or full sheet: " + value)
    return value


def render_lot(lot: dict, asset_root: Path) -> str:
    slug = lot.get("id")
    if not isinstance(slug, str) or not SLUG.fullmatch(slug):
        raise RuntimeError("PAPAUTO LOT: invalid ID " + str(slug))
    market = lot.get("market")
    if market not in MARKETS:
        raise RuntimeError("PAPAUTO LOT: invalid country " + str(market))
    if lot.get("inspection_kind") != "Аукционный лист":
        raise RuntimeError("PAPAUTO LOT: full original auction sheet required " + slug)
    desc = lot.get("description")
    if not isinstance(desc, str) or len(desc.strip()) < 100:
        raise RuntimeError("PAPAUTO LOT: verified description required " + slug)
    photos = lot.get("photos")
    if not isinstance(photos, list) or not photos:
        raise RuntimeError("PAPAUTO LOT: original auction photos missing " + slug)
    if not isinstance(lot.get("mileage_km"), int) or lot["mileage_km"] < 0:
        raise RuntimeError("PAPAUTO LOT: source-verified mileage required " + slug)
    sheet = check_media(lot.get("inspection_image"), asset_root)
    photos = [check_media(p, asset_root) for p in photos]
    if len(photos) != len(set(photos)) or sheet in photos:
        raise RuntimeError("PAPAUTO LOT: duplicate media within lot " + slug)
    region, cur, symbol = MARKETS[market]
    price_amount = lot.get("price_amount", lot.get("price_jpy", 0))
    if not isinstance(price_amount, (int, float)) or price_amount < 0:
        raise RuntimeError("PAPAUTO LOT: invalid documented price " + slug)
    if lot.get("currency", "JPY" if market == "japan" else cur) != cur:
        raise RuntimeError("PAPAUTO LOT: currency mismatch " + slug)
    sold = lot.get("status") == "sold"
    if sold and not price_amount:
        raise RuntimeError("PAPAUTO LOT: unsubstantiated winning price " + slug)
    price_text = (f"{int(price_amount):,}".replace(",", " ") + " " + symbol
                  if price_amount else "Цена продажи не подтверждена")
    date = str(lot.get("auction_date") or "")
    date_human = ".".join(reversed(date.split("-"))) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) else date
    if not date or not lot.get("lot_number") or not lot.get("auction"):
        raise RuntimeError("PAPAUTO LOT: auction identity incomplete " + slug)
    specs = [
        ("Модель и год", f"{lot['model']} · {lot['year']}"),
        ("Страна", region), ("Аукцион", lot["auction"]),
        ("Дата торгов", date_human), ("Номер лота", lot["lot_number"]),
        ("Кузов", lot.get("body") or "Не указан"),
        ("Пробег", f"{int(lot['mileage_km']):,}".replace(",", " ") + " км"),
        ("Оценка аукциона", lot.get("grade") or "Не указана"),
    ]
    if lot.get("trim"):
        specs.append(("Комплектация по источнику", lot["trim"]))
    if lot.get("steering"):
        specs.append(("Руль по источнику", lot["steering"]))
    if lot.get("engine_cc"):
        specs.append(("Двигатель по источнику", str(lot["engine_cc"]) + " см³"))
    if lot.get("power_hp"):
        specs.append(("Мощность по источнику", str(lot["power_hp"]) + " л. с."))
    fact_html = "\n".join(
        f'<div class="lot-fact"><span>{safe(k)}</span><strong>{safe(v)}</strong></div>'
        for k, v in specs
    )
    all_photos = "\n".join(
        f'<figure class="lot-photo"><a href="{safe(src)}" target="_blank" rel="noopener" '
        f'aria-label="Увеличить аукционный ракурс {i} автомобиля {safe(lot["model"])}">'
        f'<img src="{safe(src)}" alt="Аукционный ракурс {i} {safe(lot["model"])}" '
        f'loading="{("eager" if i == 1 else "lazy")}" decoding="async"></a>'
        f'<figcaption>Ракурс {i}</figcaption></figure>'
        for i, src in enumerate(photos, 1)
    )
    similar = quote(lot["model"] + " " + str(lot["year"]) + " · " + region)
    status = ("Продан на аукционе по данным источника" if sold
              else "Аукционный пример, факт продажи не подтверждён")
    warning = ("Цена аукционных торгов без доставки, таможни, утильсбора и комиссии."
               if price_amount else "Итоговую цену продажи необходимо подтвердить.")
    return f"""<!doctype html>
<html lang="ru"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,follow">
<meta name="theme-color" content="#122942">
<title>{safe(lot["model"])} {safe(lot["year"])} — аукционный лот №{safe(lot["lot_number"])} | PAPAUTO</title>
<meta name="description" content="Фотографии и полный аукционный лист {safe(lot["model"])} {safe(lot["year"])} года, пробег и оценка.">
<link rel="stylesheet" href="/lot-detail.css?v=1">
<link rel="icon" href="/assets/favicon.svg">
</head><body>
<header class="lot-header"><a class="lot-brand" href="/">PAPAUTO<span>.</span></a>
<nav><a href="/gallery.html">Вся галерея</a><a href="/catalog.html">Каталог моделей</a></nav></header>
<main class="lot-main" id="auction-lot-main">
<a class="lot-back" href="/gallery.html#gallery-lot-{safe(slug)}">← Назад к аукционным автомобилям</a>
<div class="lot-heading"><div><p class="lot-label">АУКЦИОННЫЙ ЛОТ · {safe(region.upper())}</p>
<h1>{safe(lot["model"])} <span>{safe(lot["year"])}</span></h1>
<p class="lot-status">{safe(status)} · Аукцион {safe(lot["auction"])} · Лот №{safe(lot["lot_number"])}</p></div>
<a class="lot-apply" href="/podbor.html?similar={safe(similar)}">Подобрать аналог</a></div>
<div class="lot-layout"><section aria-labelledby="lot-gallery-title">
<h2 id="lot-gallery-title">Аукционные фотографии</h2>
<p class="lot-help">Фотографии относятся к указанному лоту; нажмите на снимок для полноразмерного просмотра.</p>
<div class="lot-photos">{all_photos}</div>
<section class="lot-sheet" aria-labelledby="lot-sheet-title">
<h2 id="lot-sheet-title">Оригинальный аукционный лист</h2>
<p>Документ этого лота, не заменён схемой повреждений.</p>
<a href="{safe(sheet)}" target="_blank" rel="noopener" aria-label="Открыть полный аукционный лист {safe(lot["model"])}">
<img src="{safe(sheet)}" loading="lazy" decoding="async" alt="Полный аукционный лист {safe(lot["model"])} · №{safe(lot["lot_number"])}"></a>
</section></section>
<aside class="lot-information" aria-label="Параметры конкретного аукционного лота">
<h2>Данные автомобиля</h2><div class="lot-facts">{fact_html}</div>
<h2>Описание лота</h2><p class="lot-description">{safe(desc)}</p>
<div class="lot-price"><span>{safe("Цена торгов по источнику" if price_amount else "Итог торгов не подтверждён")}</span>
<strong>{safe(price_text)}</strong><p>{safe(warning)}</p></div>
<p class="lot-caution">Исторический аукционный пример — не подтверждение наличия автомобиля. Проверяем актуальность и стоимость аналога индивидуально.
Права на использование архивных сторонних изображений требуют отдельного подтверждения.</p>
<a class="lot-apply lot-apply-wide" href="/podbor.html?similar={safe(similar)}">Подобрать похожий автомобиль</a>
</aside></div></main>
<footer class="lot-footer"><span>PAPAUTO · Япония, Корея, Китай</span><a href="/privacy.html">Политика конфиденциальности</a></footer>
</body></html>"""


def generate(gallery: dict, target: Path, asset_root: Path | None = None) -> dict:
    target = Path(target)
    asset_root = Path(asset_root) if asset_root is not None else target
    lots = gallery.get("lots")
    if not isinstance(lots, list) or not 37 <= len(lots) <= 500:
        raise RuntimeError("PAPAUTO LOT: invalid source catalogue")
    ids = [r.get("id") for r in lots]
    if len(ids) != len(set(ids)):
        raise RuntimeError("PAPAUTO LOT: duplicate auction IDs")
    destination = target / "lots"
    destination.mkdir(parents=True, exist_ok=True)
    for record in lots:
        text = render_lot(record, asset_root)
        (destination / (record["id"] + ".html")).write_text(text, encoding="utf-8")
    return {"detail_pages": len(lots), "noindex_until_launch": True}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "data/gallery-lots.json").read_text(encoding="utf-8"))
    print(json.dumps(generate(data, root / "render-public", root), ensure_ascii=False))
