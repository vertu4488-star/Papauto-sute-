"""Fail-closed PAPAUTO auction gallery publisher, preserving 37 full-sheet archive lots.

Only new licensed full-sheet auction records are appended from the approved registry.
HTML contains factual static cards even without JS; client gets the same embedded JSON.
"""
from __future__ import annotations
import html as htmllib
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
APPROVED = ROOT / "data" / "approved-auction-lots.json"
LEDGER = ROOT / "research" / "auction-photo-rights-ledger.json"
BASELINE = 37
MAX_LOTS = 500
# Source/provenance keeps all 37 entries, but two outdoor-only records are
# never allowed in the customer-facing release (including static fallback).
QUARANTINED_OUTDOOR_LOTS = frozenset({
    "nissan-note-2021-227", "mercedes-a180-2020",
})
COUNTRY = {"japan": ("ЯПОНИЯ", "🇯🇵", "JPY"),
           "south-korea": ("КОРЕЯ", "🇰🇷", "KRW"),
           "china": ("КИТАЙ", "🇨🇳", "CNY")}
ACCEPTED_ASSET = re.compile(
    r"^/assets/(?:auction/home/[a-z0-9-]+\.jpg"
    r"|premium-auctions/[a-z0-9-]+\.webp"
    r"|auction/approved/[a-z0-9-]+\.(?:jpg|jpeg|png|webp))$")
PREMIUM_MAKES = {"audi", "bmw", "mercedes-benz", "lexus", "porsche",
                 "volvo", "jaguar", "land rover", "genesis", "infiniti"}


def assert_local(target: Path, url: str) -> None:
    if not isinstance(url, str) or not ACCEPTED_ASSET.fullmatch(url):
        raise RuntimeError("PAPAUTO_POLICY: forbidden gallery image path: " + str(url))
    file = target / url.lstrip("/")
    if not file.is_file() or file.is_symlink():
        raise RuntimeError("PAPAUTO_POLICY: missing auction photo/sheet: " + url)


def prepare_approved(target: Path, record: dict) -> dict:
    ident = record.get("id")
    if not isinstance(ident, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,75}", ident):
        raise RuntimeError("PAPAUTO_POLICY: approved lot id invalid")
    country = record.get("country")
    if country not in COUNTRY:
        raise RuntimeError("PAPAUTO_POLICY: country invalid: " + ident)
    for flag in ("commercial_use_permission", "self_host_permission", "sheet_permission"):
        if record.get(flag) is not True:
            raise RuntimeError("PAPAUTO_POLICY: unlicensed photo/sheet: " + ident)
    if record.get("image_rights") != "approved":
        raise RuntimeError("PAPAUTO_POLICY: photo rights missing: " + ident)
    for required in ("rights_holder", "rights_reference", "vehicle_evidence_reference",
                     "description", "make", "model", "auction", "lot", "grade", "auction_date"):
        if not str(record.get(required) or "").strip():
            raise RuntimeError("PAPAUTO_POLICY: missing " + required + " for " + ident)
    if len(record["description"]) < 30 or record.get("photo_context") != "original_auction_lot":
        raise RuntimeError("PAPAUTO_POLICY: no actual auction-lot description/provenance for " + ident)
    if record.get("sheet_type") != "original_auction_sheet":
        raise RuntimeError("PAPAUTO_POLICY: auction sheet not original: " + ident)
    if not isinstance(record.get("year"), int) or not 1950 <= record["year"] <= 2027:
        raise RuntimeError("PAPAUTO_POLICY: invalid year for " + ident)
    if not isinstance(record.get("mileage_km"), int) or record["mileage_km"] < 0:
        raise RuntimeError("PAPAUTO_POLICY: missing verified mileage " + ident)
    photos = record.get("photos")
    if not isinstance(photos, list) or not 1 <= len(photos) <= 15 or not record.get("auction_sheet"):
        raise RuntimeError("PAPAUTO_POLICY: authentic photo and auction sheet required " + ident)
    for url in photos + [record["auction_sheet"]]:
        if not url.startswith("/assets/auction/approved/"):
            raise RuntimeError("PAPAUTO_POLICY: new photo not in approved auction folder: " + ident)
        assert_local(target, url)
    status = record.get("sale_status")
    if status not in {"reference_only", "verified_sold"}:
        raise RuntimeError("PAPAUTO_POLICY: unknown sale result: " + ident)
    amount = 0
    currency = COUNTRY[country][2]
    if status == "verified_sold":
        if not record.get("sale_evidence_reference") or record.get("currency") != currency:
            raise RuntimeError("PAPAUTO_POLICY: sold result unverified: " + ident)
        amount = record.get("sold_price")
        if not isinstance(amount, (int, float)) or not amount > 0:
            raise RuntimeError("PAPAUTO_POLICY: sold price invalid: " + ident)
    make = str(record["make"]).strip()
    model = str(record["model"]).strip()
    return {
        "id": ident, "origin": "approved", "market": country,
        "model": make + " " + model, "year": record["year"],
        "mileage_km": record["mileage_km"], "body": record.get("body", ""),
        "grade": str(record["grade"]), "auction": record["auction"],
        "lot_number": str(record["lot"]), "auction_date": record["auction_date"],
        "price_amount": amount, "currency": currency,
        "status": "sold" if status == "verified_sold" else "reference_only",
        "sale_label": ("Продан на аукционе" if status == "verified_sold"
                       else "Аукционный лот, цена продажи не подтверждена"),
        "photos": photos, "inspection_image": record["auction_sheet"],
        "inspection_kind": "Аукционный лист",
        "category": ("premium" if make.lower() in PREMIUM_MAKES else "popular"),
        "rights_confirmed": True, "export_restricted": False,
        "description": record["description"][:1200]
    }


def static_card(lot: dict) -> str:
    e = lambda s: htmllib.escape(str(s), quote=True)
    name = lot["model"]
    first = lot["photos"][0]
    sheet = lot["inspection_image"]
    country, icon, _ = COUNTRY[lot["market"]]
    price = (f"{int(lot['price_amount']):,}".replace(",", " ") +
             " " + {"JPY": "¥", "KRW": "₩", "CNY": "¥"}[lot["currency"]]
             if lot["price_amount"] else "Цена продажи не подтверждена")
    note = "Цена торгов, без доставки" if lot["price_amount"] else "Оценка цены — по запросу"
    similar = quote(name + " " + str(lot["year"]) + " · " + country)
    return (
        f'<article class="gallery-card" id="gallery-lot-{e(lot["id"])}" '
        f'data-lot-id="{e(lot["id"])}" data-gallery-category="{e(lot["category"])}">\n'
        f'<div class="gallery-card-head"><span class="gallery-market">{icon} {country} · АУКЦИОН</span>'
        f'<span class="gallery-grade">Оценка {e(lot["grade"])}</span></div>\n'
        f'<a class="gallery-card-photo" href="{e(first)}" aria-label="Фото {e(name)}">'
        f'<img loading="lazy" decoding="async" src="{e(first)}" alt="Фото аукционного лота {e(name)}">'
        f'<span class="gallery-photo-indicator">Ракурс 1</span></a>\n'
        f'<div class="gallery-thumbnails"><a class="gallery-thumb" href="{e(sheet)}" '
        f'aria-label="Аукционный лист {e(name)}">'
        f'<img loading="lazy" decoding="async" src="{e(sheet)}" alt="Аукционный лист {e(name)}"></a></div>\n'
        f'<div class="gallery-card-body"><h3>{e(name)} · {lot["year"]}</h3>'
        f'<p class="gallery-variant">{e(lot["sale_label"])}</p>'
        f'<p class="gallery-description">{e(lot["description"])}</p>'
        f'<div class="gallery-facts"><div class="gallery-fact"><span>Пробег</span>'
        f'<strong>{int(lot["mileage_km"]):,} км</strong></div>'
        f'<div class="gallery-fact"><span>Аукцион</span><strong>{e(lot["auction"])}</strong></div>'
        f'<div class="gallery-fact"><span>Кузов</span><strong>{e(lot["body"] or "—")}</strong></div>'
        f'<div class="gallery-fact"><span>Дата / № лота</span>'
        f'<strong>{e(lot["auction_date"])} · {e(lot["lot_number"])}</strong></div></div>'
        f'<div class="gallery-price"><span>{note}</span><strong>{price}</strong></div></div>\n'
        f'<div class="gallery-card-footer"><a class="gallery-full" href="/lots/{e(lot["id"])}.html">'
        f'Подробная карточка лота</a><a class="gallery-detail" href="{e(sheet)}">'
        f'Аукционный лист</a><a class="gallery-apply" href="/podbor.html?similar={similar}">'
        f'Подобрать аналог</a></div></article>\n'
    )


def compile_published_gallery(target: Path, approved_path: Path = APPROVED,
                              ledger_path: Path = LEDGER) -> dict:
    registry_path = target / "data" / "gallery-lots.json"
    page_path = target / "gallery.html"
    gallery = json.loads(registry_path.read_text(encoding="utf-8"))
    base = gallery.get("lots", [])
    if len(base) != BASELINE:
        raise RuntimeError("PAPAUTO_POLICY: expected the 37 complete-sheet auction records")
    ids = {r["id"] for r in base}
    if len(ids) != BASELINE:
        raise RuntimeError("PAPAUTO_POLICY: duplicate base lot ID")
    if not QUARANTINED_OUTDOOR_LOTS.issubset(ids):
        raise RuntimeError("PAPAUTO_POLICY: expected quarantined provenance records missing")
    source_baseline_ids = ids.copy()
    # Reject identified outdoor imagery BEFORE validating/using public asset paths.
    # Keep full unmodified records in private research and source JSON.
    base = [r for r in base if r["id"] not in QUARANTINED_OUTDOOR_LOTS]
    trimmed = 0
    for lot in base:
        photos = lot.get("photos") or []
        if not photos:
            raise RuntimeError("PAPAUTO_POLICY: no main photo " + lot["id"])
        if lot.get("inspection_kind") != "Аукционный лист":
            raise RuntimeError("PAPAUTO_POLICY: full auction sheet is mandatory: " + lot["id"])
        assert_local(target, photos[0])
        assert_local(target, lot["inspection_image"])
        available = [p for p in photos if ACCEPTED_ASSET.fullmatch(p)
                     and (target / p.lstrip("/")).is_file()]
        trimmed += len(photos) - len(available)
        lot["photos"] = available
    approved = json.loads(approved_path.read_text(encoding="utf-8")).get("lots", [])
    if not isinstance(approved, list) or len(approved) + BASELINE > MAX_LOTS:
        raise RuntimeError("PAPAUTO_POLICY: approved count exceeds gallery limit of 500")
    # The private rights ledger is mandatory when adding licensed lots.
    # Do not accept directly edited/public-only records that bypassed the importer.
    if approved:
        if not ledger_path.is_file():
            raise RuntimeError("PAPAUTO_POLICY: private photo-rights ledger missing")
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        rights_rows = ledger.get("lots", [])
        rights = {r["id"]: r for r in rights_rows}
        if len(rights) != len(rights_rows):
            raise RuntimeError("PAPAUTO_POLICY: duplicate rights evidence records")
        used_hashes = {}
        for rec in approved:
            right = rights.get(rec["id"])
            if (right is None or right.get("license_evidence") != rec.get("rights_reference")
                    or right.get("license_holder") != rec.get("rights_holder")):
                raise RuntimeError("PAPAUTO_POLICY: license provenance not in private ledger: " + rec["id"])
            media = rec["photos"] + [rec["auction_sheet"]]
            digest_list = [hashlib.sha256((target / url.lstrip("/")).read_bytes()).hexdigest()
                           for url in media]
            if digest_list != right.get("photo_sha256"):
                raise RuntimeError("PAPAUTO_POLICY: altered photo or sheet: " + rec["id"])
            for sha in digest_list:
                if sha in used_hashes and used_hashes[sha] != rec["id"]:
                    raise RuntimeError("PAPAUTO_POLICY: photo reused in distinct auction lots")
                used_hashes[sha] = rec["id"]
    additional = [prepare_approved(target, rec) for rec in approved]
    seen_lot_keys = {
        (r["market"], r["auction"], str(r["auction_date"]), str(r["lot_number"]))
        for r in base
    }
    for r in additional:
        if r["id"] in ids:
            raise RuntimeError("PAPAUTO_POLICY: duplicate ID " + r["id"])
        ids.add(r["id"])
        key = (r["market"], r["auction"], r["auction_date"], r["lot_number"])
        if key in seen_lot_keys:
            raise RuntimeError("PAPAUTO_POLICY: duplicate auction house/date/number " + r["id"])
        seen_lot_keys.add(key)
    gallery["lots"] = base + additional
    gallery["lot_count"] = len(gallery["lots"])
    page = page_path.read_text(encoding="utf-8")
    boot = r'(<script[^>]*id="gallery-bootstrap"[^>]*>)(.*?)(</script>)'
    hit = re.search(boot, page, flags=re.S)
    if not hit:
        raise RuntimeError("PAPAUTO_POLICY: embedded auction gallery registry missing")
    original = json.loads(hit.group(2))
    if {r["id"] for r in original.get("lots", [])} != source_baseline_ids:
        raise RuntimeError("PAPAUTO_POLICY: unexpected source page gallery IDs")
    # Remove static HTML cards as well: without JS, outdoor lots must be absent.
    # Never replace outdoor images with random stock/dealer placeholders.
    for rejected in sorted(QUARANTINED_OUTDOOR_LOTS):
        pattern = (r'<article class="gallery-card" id="gallery-lot-'
                   + re.escape(rejected) + r'"[^>]*>.*?</article>\s*')
        page, count = re.subn(pattern, "", page, count=1, flags=re.S)
        if count != 1:
            raise RuntimeError("PAPAUTO_POLICY: outdoor static card not found " + rejected)
    hit = re.search(boot, page, flags=re.S)
    if additional:
        before = page[:hit.start()]
        end_of_grid = before.rfind("</div>")
        if end_of_grid < before.find('<div class="gallery-grid" id="gallery-grid">'):
            raise RuntimeError("PAPAUTO_POLICY: no static gallery card grid to expand")
        new_cards = "\n" + "".join(static_card(r) for r in additional)
        page = page[:end_of_grid] + new_cards + page[end_of_grid:]
        # Refresh the inline data match after inserting cards.
        hit = re.search(boot, page, flags=re.S)
    total = len(gallery["lots"])
    premium_count = sum(r.get("category") == "premium" for r in gallery["lots"])
    popular_count = total - premium_count
    page = page.replace("Все 37</button>", f"Все {total}</button>", 1)
    page = page.replace("Премиальные · 14</button>",
                        f"Премиальные · {premium_count}</button>", 1)
    page = page.replace("Популярные · 23</button>",
                        f"Популярные · {popular_count}</button>", 1)
    page = page.replace("<strong>37</strong>", f"<strong>{total}</strong>", 1)
    page = page.replace("<strong>25</strong>",
                        f"<strong>{sum(r['origin'] == 'home' for r in base)}</strong>", 1)
    page = page.replace("<strong>12</strong>",
                        f"<strong>{sum(r['origin'] == 'premium' for r in base)}</strong>", 1)
    page = page.replace("Фото и документы 37 конкретных японских аукционных лотов",
                        f"Фото и документы {total} конкретных японских аукционных лотов", 1)
    page = page.replace("Все страны (37)", f"Все страны ({total})", 1)
    page = page.replace("37 разных лотов", f"{total} разных лотов", 1)
    page = page.replace("37 аукционных автомобилей · все карточки доступны",
                        f"{total} аукционных автомобилей · все карточки доступны", 1)
    page = page.replace("37 примеров автомобилей", f"{total} примеров автомобилей", 1)
    page = page.replace("— 37 лотов", f"— {total} лотов", 1)
    hit = re.search(boot, page, flags=re.S)
    if not hit:
        raise RuntimeError("PAPAUTO_POLICY: lost embedded registry during processing")
    embedded = json.dumps(gallery, ensure_ascii=False, separators=(",", ":"))
    embedded = embedded.replace("<", "\\u003c")
    page = page[:hit.start(2)] + embedded + page[hit.end(2):]
    page_path.write_text(page, encoding="utf-8")
    registry_path.write_text(json.dumps(gallery, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    try:
        from scripts.generate_auction_lot_pages import generate
    except ModuleNotFoundError:
        from generate_auction_lot_pages import generate
    generated = generate(gallery, target)
    return {"count": total, "new": len(additional), "skipped_optional": trimmed,
            "detail_pages": generated["detail_pages"]}
