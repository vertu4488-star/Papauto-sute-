"""Fail-closed PAPAUTO auction gallery publisher, preserving 37 full-sheet archive lots.

Licensed records and the single owner-selected batch use distinct publication records.
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
OWNER_SELECTION = ROOT / "research" / "owner-selected-japan-lots-2026-11-14.json"
BASELINE = 37
MAX_LOTS = 700
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


def prepare_approved(target: Path, record: dict, *, owner_selected: bool = False) -> dict:
    ident = record.get("id")
    if not isinstance(ident, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,75}", ident):
        raise RuntimeError("PAPAUTO_POLICY: approved lot id invalid")
    country = record.get("country")
    if country not in COUNTRY:
        raise RuntimeError("PAPAUTO_POLICY: country invalid: " + ident)
    required_fields = ("description", "make", "model", "auction", "lot", "grade", "auction_date")
    if not owner_selected:
        for flag in ("commercial_use_permission", "self_host_permission", "sheet_permission"):
            if record.get(flag) is not True:
                raise RuntimeError("PAPAUTO_POLICY: unlicensed photo/sheet: " + ident)
        if record.get("image_rights") != "approved":
            raise RuntimeError("PAPAUTO_POLICY: photo rights missing: " + ident)
        required_fields += ("rights_holder", "rights_reference", "vehicle_evidence_reference")
    for required in required_fields:
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
    if owner_selected:
        media = photos + [record["auction_sheet"]]
        actual = [hashlib.sha256((target / url.lstrip("/")).read_bytes()).hexdigest() for url in media]
        if actual != record.get("media_sha256") or len(set(actual)) != len(actual):
            raise RuntimeError("PAPAUTO_POLICY: owner-selected media mismatch: " + ident)
        amount = record.get("reported_price")
        if type(amount) is not int or amount <= 0 or country != "japan" or status != "reference_only":
            raise RuntimeError("PAPAUTO_POLICY: invalid owner-selected reference price: " + ident)
    make = str(record["make"]).strip()
    model = str(record["model"]).strip()
    return {
        "id": ident, "origin": "owner_selection" if owner_selected else "approved", "market": country,
        "model": make + " " + model, "year": record["year"],
        "mileage_km": record["mileage_km"], "body": record.get("body", ""),
        "grade": str(record["grade"]), "auction": record["auction"],
        "lot_number": str(record["lot"]), "auction_date": record["auction_date"],
        "price_amount": amount, "currency": currency,
        "status": "sold" if status == "verified_sold" else "reference_only",
        "sale_label": ("Продан на аукционе" if status == "verified_sold"
                       else "Цена по данным аукциона" if owner_selected
                       else "Аукционный лот, цена продажи не подтверждена"),
        "photos": photos, "inspection_image": record["auction_sheet"],
        "inspection_kind": "Аукционный лист",
        "category": ("premium" if make.lower() in PREMIUM_MAKES else "popular"),
        "rights_confirmed": not owner_selected, "export_restricted": False,
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
    if lot["origin"] == "owner_selection":
        note = "Цена по данным аукциона"
    else:
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
                              ledger_path: Path = LEDGER, *,
                              owner_path: Path | None = None) -> dict:
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
        raise RuntimeError("PAPAUTO_POLICY: approved count exceeds gallery limit of 700")
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
    if owner_path is not None:
        # The owner approved the exact 100-card PDF on Nov 15: 97 selected source
        # records plus three existing historic lots. Reject ALL other source
        # records (even if they have photo files) before serving them.
        receipt = json.loads(
            (ROOT / "research/owner-approved-100-release-2026-11-15.json")
            .read_text(encoding="utf-8")
        )
        source_rows = json.loads(owner_path.read_text(encoding="utf-8"))["lots"]
        approved_new = receipt["approved_new_owner_selected_ids"]
        approved_old = receipt["approved_existing_public_ids"]
        denied = receipt["excluded_unreviewed_selected_ids"]
        if (len(source_rows) != 100 or len(approved_new) != 97
                or len(approved_old) != 3 or len(denied) != 3
                or receipt.get("approved_count") != 100
                or len({*approved_new, *approved_old, *denied}) != 103
                or len(base) + len(additional) + len(approved_new) > MAX_LOTS
                or not set(approved_old).issubset({r["id"] for r in base})):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: reviewed PDF lot IDs mismatch")
        source_by_id = {r["id"]: r for r in source_rows}
        if (len(source_by_id) != 100
                or set(source_by_id) != set(approved_new) | set(denied)
                or any(str(source_by_id[id_].get("grade", "")).strip() not in {"", "—", "*"}
                       for id_ in denied)
                or any(str(source_by_id[id_].get("grade", "")).strip() in {"", "—", "*"}
                       for id_ in approved_new)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: selected records changed")
        selection = [source_by_id[id_] for id_ in approved_new]
        media_hashes = [digest for row in selection for digest in row["media_sha256"]]
        if len(set(media_hashes)) != 194 or len(media_hashes) != 194:
            raise RuntimeError("PAPAUTO_POLICY: repeated reviewed photo/auction sheet")
        additional.extend(prepare_approved(target, row, owner_selected=True) for row in selection)
        # Exact second owner-authorized archival release; no general import permission.
        archive = json.loads((ROOT / "research/owner-approved-50-archive-2026-11-19.json").read_text(encoding="utf-8"))
        archived = archive["lots"]
        if (archive.get("approved_count") != 50 or archive.get("rights_confirmed") is not False
                or archive.get("owner_authorized_archival_reference_only") is not True
                or archive.get("reviewed_pdf_sha256") != "7c4c0c775dbcf3f4ca6f8f967282d66e6692f147b02d4ce74b67bcdb614746a6"
                or [r["id"] for r in archived] != [f"japan-archive-20261119-{i:02d}" for i in range(1,51)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: 50-card archive receipt mismatch")
        hashes = [h for r in archived for h in r["media_sha256"]]
        if len(hashes) != 150 or len(set(hashes + media_hashes)) != 344:
            raise RuntimeError("PAPAUTO_POLICY: duplicate reviewed media")
        for rec in archived:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
        # Second exact 50-card owner-reviewed release, separate from prior batch.
        archive2 = json.loads((ROOT / "research/owner-approved-second-50-archive-2026-11-19.json").read_text(encoding="utf-8"))
        archived2 = archive2["lots"]
        if (archive2.get("approved_count") != 50 or archive2.get("rights_confirmed") is not False
                or archive2.get("owner_authorized_archival_reference_only") is not True
                or archive2.get("reviewed_pdf_sha256") != "8f9f0e37d605e5f4faced72994f4c9e246c02d886b213a379dfcd3acd18ac9bc"
                or archive2.get("raw_media_aggregate_sha256") != "53d5b85abd81282fb0e37e169617da7a08eb7562a5f77d35ab127e073432065b"
                or [r["id"] for r in archived2] != [f"japan-archive-b2-20261119-{i:02d}" for i in range(1,51)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived2)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: second archive review mismatch")
        hashes2 = [h for r in archived2 for h in r["media_sha256"]]
        if len(hashes2) != 150 or len(set(hashes2 + hashes + media_hashes)) != 494:
            raise RuntimeError("PAPAUTO_POLICY: duplicate second batch media")
        for rec in archived2:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
        # Exact ATP thirty-card owner-reviewed reference release.
        archive3 = json.loads((ROOT / "research/owner-approved-japan-atp-30-archive-2026-11-20.json").read_text(encoding="utf-8"))
        archived3 = archive3["lots"]
        if (archive3.get("approved_count") != 30 or archive3.get("rights_confirmed") is not False
                or archive3.get("owner_authorized_archival_reference_only") is not True
                or archive3.get("reviewed_pdf_sha256") != "e1969418135a27745c996be11f5a95b5b5564441c61c7c906d1b1d56d354adc2"
                or [r["id"] for r in archived3] != [f"japan-atp-20261120-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived3)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: ATP archive review mismatch")
        hashes3 = [h for r in archived3 for h in r["media_sha256"]]
        if len(hashes3) != 90 or len(set(hashes3 + hashes2 + hashes + media_hashes)) != 584 or hashlib.sha256("".join(hashes3).encode()).hexdigest() != "4c1d0949833b3ae47dc42276101f550de7403d1803a04c931106a09cae769286":
            raise RuntimeError("PAPAUTO_POLICY: ATP reviewed media mismatch")
        for rec in archived3:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
        # Exact ATP thirty-card owner-reviewed reference release.
        archive4 = json.loads((ROOT / "research/owner-approved-japan-atp-second-30-archive-2026-11-20.json").read_text(encoding="utf-8"))
        archived4 = archive4["lots"]
        if (archive4.get("approved_count") != 30 or archive4.get("rights_confirmed") is not False
                or archive4.get("owner_authorized_archival_reference_only") is not True
                or archive4.get("reviewed_pdf_sha256") != "ef50db28dc98dd71734361b1bc67ab6b6d642414e449be755b2142c2ef43cad8"
                or [r["id"] for r in archived4] != [f"japan-atp-b2-20261120-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived4)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: ATP archive review mismatch")
        hashes4 = [h for r in archived4 for h in r["media_sha256"]]
        if len(hashes4) != 90 or len(set(hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 674 or hashlib.sha256("".join(hashes4).encode()).hexdigest() != "8019e79ca9982958ea5fe8d3f88d6810fabe14a62d9d71f5cb172a8fe8b0edf2":
            raise RuntimeError("PAPAUTO_POLICY: ATP reviewed media mismatch")
        for rec in archived4:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
        # Exact ATP thirty-card owner-reviewed reference release.
        archive5 = json.loads((ROOT / "research/owner-approved-japan-atp-third-30-archive-2026-11-20.json").read_text(encoding="utf-8"))
        archived5 = archive5["lots"]
        if (archive5.get("approved_count") != 30 or archive5.get("rights_confirmed") is not False
                or archive5.get("owner_authorized_archival_reference_only") is not True
                or archive5.get("reviewed_pdf_sha256") != "dc6900f4b1a2f8576795d788975b825c9375dfdab6f61f766b57d27903c3ca9c"
                or [r["id"] for r in archived5] != [f"japan-atp-b3-20261120-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived5)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: ATP archive review mismatch")
        hashes5 = [h for r in archived5 for h in r["media_sha256"]]
        if len(hashes5) != 90 or len(set(hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 764 or hashlib.sha256("".join(hashes5).encode()).hexdigest() != "034ff7aee9a956508f906ba7f393b00772fca30562979a6fb22ef0bdc8aa411a":
            raise RuntimeError("PAPAUTO_POLICY: ATP reviewed media mismatch")
        for rec in archived5:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
        # Exact ATP thirty-card owner-reviewed reference release.
        archive6 = json.loads((ROOT / "research/owner-approved-japan-atp-fourth-30-archive-2026-11-20.json").read_text(encoding="utf-8"))
        archived6 = archive6["lots"]
        if (archive6.get("approved_count") != 30 or archive6.get("rights_confirmed") is not False
                or archive6.get("owner_authorized_archival_reference_only") is not True
                or archive6.get("reviewed_jpg_zip_sha256") != "3eaa53d43a421fe106cf9c70b7d9740024304951d6ee8fb695048ed13d83348d"
                or [r["id"] for r in archived6] != [f"japan-atp-b4-20261120-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived6)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: ATP archive review mismatch")
        hashes6 = [h for r in archived6 for h in r["media_sha256"]]
        if len(hashes6) != 90 or len(set(hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 854 or hashlib.sha256("".join(hashes6).encode()).hexdigest() != "2bd89b382d8e6a0748bef40ff6852018c048534c34f3fd87e56e568c6696db3f":
            raise RuntimeError("PAPAUTO_POLICY: ATP reviewed media mismatch")
        for rec in archived6:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
        # Exact ATP thirty-card owner-reviewed reference release.
        archive7 = json.loads((ROOT / "research/owner-approved-japan-atp-fifth-30-archive-2026-11-20.json").read_text(encoding="utf-8"))
        archived7 = archive7["lots"]
        if (archive7.get("approved_count") != 30 or archive7.get("rights_confirmed") is not False
                or archive7.get("owner_authorized_archival_reference_only") is not True
                or archive7.get("reviewed_jpg_zip_sha256") != "05b2637633b0233d6cc8c9356fb799be8a507717f9a4db97cad38ac6e99b43e6"
                or [r["id"] for r in archived7] != [f"japan-atp-b5-20261120-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived7)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: ATP archive review mismatch")
        hashes7 = [h for r in archived7 for h in r["media_sha256"]]
        if len(hashes7) != 90 or len(set(hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 944 or hashlib.sha256("".join(hashes7).encode()).hexdigest() != "2fa31077037843840bd658e0d4da3ff11f4e06aca2f15b114ca375c237d72346":
            raise RuntimeError("PAPAUTO_POLICY: ATP reviewed media mismatch")
        for rec in archived7:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
        # Exact ATP thirty-card owner-reviewed reference release.
        archive8 = json.loads((ROOT / "research/owner-approved-japan-atp-sixth-30-archive-2026-11-21.json").read_text(encoding="utf-8"))
        archived8 = archive8["lots"]
        if (archive8.get("approved_count") != 30 or archive8.get("rights_confirmed") is not False
                or archive8.get("owner_authorized_archival_reference_only") is not True
                or archive8.get("reviewed_jpg_zip_sha256") != "298d7269884a28dbc14505d46149615dc5bf9cbb4b30f3f18ab40d08b807e121"
                or [r["id"] for r in archived8] != [f"japan-atp-b6-20261121-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived8)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: ATP archive review mismatch")
        hashes8 = [h for r in archived8 for h in r["media_sha256"]]
        if len(hashes8) != 90 or len(set(hashes8 + hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 1034 or hashlib.sha256("".join(hashes8).encode()).hexdigest() != "5e057a358b0e1adc74975716eaa42b0940ce322aaf2932d5f0d49c004ef62355":
            raise RuntimeError("PAPAUTO_POLICY: ATP reviewed media mismatch")
        for rec in archived8:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
        # Exactly seventeen user-directed genuine Drom-priority Japanese auction archive examples.
        archive9 = json.loads((ROOT / "research/owner-approved-japan-drom991-gap-17-archive-2026-11-21.json").read_text(encoding="utf-8"))
        archived9 = archive9["lots"]
        if (archive9.get("approved_count") != 17 or archive9.get("rights_confirmed") is not False
                or archive9.get("owner_authorized_archival_reference_only") is not True
                or archive9.get("reviewed_jpg_zip_sha256") != "cff3e9449482429946d741008dd5056dc8117d6bf241688d1f928dc6cfe74de8"
                or [r["id"] for r in archived9] != [f"japan-drom991-gap-20261121-{i:02d}" for i in range(1,18)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived9)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: exact Drom-priority source photo-sheet archive mismatch")
        hashes9 = [h for r in archived9 for h in r["media_sha256"]]
        if len(hashes9) != 51 or len(set(hashes9 + hashes8 + hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 1085 or hashlib.sha256("".join(hashes9).encode()).hexdigest() != "7b3dcbded01e63464131da937f8b41c020ccf8aea56081bff3e413d012c8b75a":
            raise RuntimeError("PAPAUTO_POLICY: Drom-priority gallery media mismatch")
        for rec in archived9:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
        # Exact 30 Japan lots approved from PDF and byte-identical ZIP review.
        archive10 = json.loads((ROOT / "research/owner-approved-japan-next30-2026-11-21.json").read_text(encoding="utf-8"))
        archived10 = archive10["lots"]
        if (archive10.get("approved_count") != 30 or archive10.get("rights_confirmed") is not False
                or archive10.get("owner_authorized_archival_reference_only") is not True
                or archive10.get("reviewed_pdf_sha256") != "10ada138484429afc4de3fa1d850426a8d03b3821cc3f9abe97f8d4f99f2de7e"
                or archive10.get("reviewed_jpg_zip_sha256") != "626fe77598b0d6038fc416bcc2cc355874c03b759ce4b92f38b0912402a18473"
                or [r["id"] for r in archived10] != [f"japan-next30-drom991-20261121-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived10)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: next30 owner-approved PDF mismatch")
        hashes10 = [h for r in archived10 for h in r["media_sha256"]]
        if (len(hashes10) != 90 or len(set(hashes10 + hashes9 + hashes8 + hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 1175
                or hashlib.sha256("".join(hashes10).encode()).hexdigest() != "a9159cfaba8efb822fd1d0705443833b076736876c015a58c5ae945e452523f4"):
            raise RuntimeError("PAPAUTO_POLICY: next30 original photos/sheets mismatch or duplicates")
        for rec in archived10:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
        # Owner-directed thirty additional exact-source Japan auction reference examples.
        archive11 = json.loads((ROOT / "research/owner-approved-japan-followup30-2026-11-21.json").read_text(encoding="utf-8"))
        archived11 = archive11["lots"]
        if (archive11.get("approved_count") != 30 or archive11.get("rights_confirmed") is not False
                or archive11.get("owner_authorized_archival_reference_only") is not True
                or archive11.get("reviewed_pdf_sha256") != "01c7362b9575b09db0157b0e66189d8b518fc3037481b25d924d34ca72a9c29a"
                or archive11.get("reviewed_jpg_zip_sha256") != "218466b04049b91abe543e23c00572ac1f63f6cc6b3c5b3ac8ab441179f35a7e"
                or [r["id"] for r in archived11] != [f"japan-followup30-20261121-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived11)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: exact owner-directed next30 photo+sheet digest mismatch")
        hashes11 = [h for r in archived11 for h in r["media_sha256"]]
        if (len(hashes11) != 90
                or len(set(hashes11 + hashes10 + hashes9 + hashes8 + hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 1265
                or hashlib.sha256("".join(hashes11).encode()).hexdigest() != "be9ffa7575b7e8cf707c952e95098f8b51880d59c169a28418ed91172660dc64"):
            raise RuntimeError("PAPAUTO_POLICY: thirty additional original JPEGs/damage sheets duplicate or tampered")
        for rec in archived11:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
        # Owner-approved Japanese batch 489 -> 519, exact 30 reviewed in PDF.
        archive12 = json.loads((ROOT / "research/owner-approved-japan-next30-519-2026-11-21.json").read_text(encoding="utf-8"))
        archived12 = archive12["lots"]
        if (archive12.get("approved_count") != 30 or archive12.get("rights_confirmed") is not False
                or archive12.get("owner_authorized_archival_reference_only") is not True
                or archive12.get("reviewed_pdf_sha256") != "718076fc478c085c2df5b2197c498618ea8dc8cc59bf90dea3efd773409f3a5b"
                or archive12.get("reviewed_jpg_zip_sha256") != "61c618dbb89ed51866a9ed9618c6f7bed769a0fb2e2b0d2de8a3072c13ee8292"
                or [r["id"] for r in archived12] != [f"japan-next30-519-20261121-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived12)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: 519 reviewed PDF/media mismatch")
        hashes12 = [h for r in archived12 for h in r["media_sha256"]]
        if (len(hashes12) != 90 or len(set(hashes12 + hashes11 + hashes10 + hashes9 + hashes8 + hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 1355
                or hashlib.sha256("".join(hashes12).encode()).hexdigest() != "78d1cfa459e5f0eb0385ffcecaaff4ba8e694f0034a790730258d89015d141b9"):
            raise RuntimeError("PAPAUTO_POLICY: 519 photo / sheet media not exact reviewed originals")
        for rec in archived12:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
        # Exact 30 user-approved Japan examples after separate 519 release.
        archive13 = json.loads((ROOT / "research/owner-approved-japan-next30-549-2026-11-21.json").read_text(encoding="utf-8"))
        archived13 = archive13["lots"]
        if (archive13.get("approved_count") != 30 or archive13.get("rights_confirmed") is not False
                or archive13.get("owner_authorized_archival_reference_only") is not True
                or archive13.get("reviewed_pdf_sha256") != "7f1209ab57d0fa02acea28fdb33bb82d91f3c1a7027dcefb563da057265aa024"
                or archive13.get("reviewed_jpg_zip_sha256") != "405bb0643dc4baf67f67ff92f0e51a67e62d5b77b1e391005dbccf8e9ac33242"
                or [r["id"] for r in archived13] != [f"japan-next30-549-20261121-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived13)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: 549 PDF/ZIP or media mis-match")
        hashes13 = [h for r in archived13 for h in r["media_sha256"]]
        if (len(hashes13) != 90 or len(set(hashes13 + hashes12 + hashes11 + hashes10 + hashes9 + hashes8 + hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 1445
                or hashlib.sha256("".join(hashes13).encode()).hexdigest() != "14335eb0d5d9ec636a49ee0d9001f595bebf32ef18b060ebcce69a45e9e3589f"):
            raise RuntimeError("PAPAUTO_POLICY: duplicate or tampered 549 original source photo / sheet")
        for rec in archived13:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
        # Exact owner-approved 30 Japanese archive records: 549 -> 579.
        archive14 = json.loads((ROOT / "research/owner-approved-japan-next30-579-2026-11-21.json").read_text(encoding="utf-8"))
        archived14 = archive14["lots"]
        if (archive14.get("approved_count") != 30 or archive14.get("rights_confirmed") is not False
                or archive14.get("owner_authorized_archival_reference_only") is not True
                or archive14.get("reviewed_pdf_sha256") != "7646d44301e6a06eca031ce19a7817eea5fdebe9162793319cd998118515547a"
                or archive14.get("reviewed_jpg_zip_sha256") != "17630d57b1d090b632b3c40648b54ff2a7ec7407ddbc8a78b60b6b76d4c19b70"
                or [r["id"] for r in archived14] != [f"japan-next30-579-20261121-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived14)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: 579 immutable PDF/ZIP or source mismatch")
        hashes14 = [h for r in archived14 for h in r["media_sha256"]]
        if (len(hashes14) != 90 or len(set(hashes14 + hashes13 + hashes12 + hashes11 + hashes10 + hashes9 + hashes8 + hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 1535
                or hashlib.sha256("".join(hashes14).encode()).hexdigest() != "44a0d47f5f160fcbc6081cb522288b6dc0a9c37ebd8d687153b7624bfd724cb6"):
            raise RuntimeError("PAPAUTO_POLICY: 579 image/sheet originals tampered or reused")
        for rec in archived14:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
        # Exact owner-approved 30 Japanese archive records: 579 -> 609.
        archive15 = json.loads((ROOT / "research/owner-approved-japan-next30-609-2026-11-21.json").read_text(encoding="utf-8"))
        archived15 = archive15["lots"]
        if (archive15.get("approved_count") != 30 or archive15.get("rights_confirmed") is not False
                or archive15.get("owner_authorized_archival_reference_only") is not True
                or archive15.get("reviewed_pdf_sha256") != "43d7b575189e76ce32d1d52216f8e10aabeed49b3830b0322da18bfa2e7ab574"
                or archive15.get("reviewed_jpg_zip_sha256") != "6cc9c1f9bb3bfebfca1898e65eb8a51d4bb5d925149bffef261fdb1ba755c8c7"
                or [r["id"] for r in archived15] != [f"japan-next30-609-20261121-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived15)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: 609 immutable PDF/ZIP or source mismatch")
        hashes15 = [h for r in archived15 for h in r["media_sha256"]]
        if (len(hashes15) != 90 or len(set(hashes15 + hashes14 + hashes13 + hashes12 + hashes11 + hashes10 + hashes9 + hashes8 + hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 1625
                or hashlib.sha256("".join(hashes15).encode()).hexdigest() != "c7312b26bfdaf738a7a4b004285f0554201490dcce620a7ebdcead5aef1689e4"):
            raise RuntimeError("PAPAUTO_POLICY: 609 image/sheet originals tampered or reused")
        for rec in archived15:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
        # Exact owner-approved 30 Japanese archive records: 609 -> 639.
        archive16 = json.loads((ROOT / "research/owner-approved-japan-next30-639-2026-11-21.json").read_text(encoding="utf-8"))
        archived16 = archive16["lots"]
        if (archive16.get("approved_count") != 30 or archive16.get("rights_confirmed") is not False
                or archive16.get("owner_authorized_archival_reference_only") is not True
                or archive16.get("reviewed_pdf_sha256") != "2d814fb54e9acced643bcba53b61094bee4256eb4576c6dedd590c9ca65ddc76"
                or archive16.get("reviewed_jpg_zip_sha256") != "fa60be07638523672d19c41eb68f16fd91e3fcd1488870544b8c3b1337d20c47"
                or [r["id"] for r in archived16] != [f"japan-next30-639-20261121-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived16)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: 639 immutable PDF/ZIP or source mismatch")
        hashes16 = [h for r in archived16 for h in r["media_sha256"]]
        if (len(hashes16) != 90 or len(set(hashes16 + hashes15 + hashes14 + hashes13 + hashes12 + hashes11 + hashes10 + hashes9 + hashes8 + hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 1715
                or hashlib.sha256("".join(hashes16).encode()).hexdigest() != "fedd01f9183b25bddbd40414f9766ee273021e05b29ccb93a01b11b1fedac458"):
            raise RuntimeError("PAPAUTO_POLICY: 639 image/sheet originals tampered or reused")
        for rec in archived16:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
        archive17 = json.loads((ROOT / "research/owner-approved-japan-drom991-14-2026-11-21.json").read_text(encoding="utf-8"))
        if archive17.get("approved_count") != 2 or archive17.get("rights_confirmed") is not False:
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: Japan 14")
        for rec in archive17["lots"]:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(engine_cc=rec["engine_cc"], power_hp=rec["power_hp"], sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
        archive18 = json.loads((ROOT / "research/owner-approved-japan-gap18-2026-11-25.json").read_text(encoding="utf-8"))
        archived18 = archive18["lots"]
        if (archive18.get("approved_count") != 18 or archive18.get("rights_confirmed") is not False
                or archive18.get("owner_authorized_archival_reference_only") is not True
                or archive18.get("reviewed_pdf_sha256") != "3b8b5ed6adb46bf5ac23d52c8a3e08f760f9352df6809d5fc3ee8cc00dbb8154"
                or archive18.get("reviewed_jpg_zip_sha256") != "4984e9ac975f41a7087e5a0bee25b2a137dd7030a4844ffc9532c55c8d6f4533"
                or archive18.get("reviewed_full_manifest_sha256") != "eb9ddd1cd10667393075f289e530d02633a8f101f8f2c0afff2390a11e36bfd9"
                or [r["id"] for r in archived18] != [f"japan-gap18-20261125-{i:02d}" for i in range(1,19)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived18)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: exact 18 archive receipt mismatch")
        hashes18 = [h for r in archived18 for h in r["media_sha256"]]
        prior18 = hashes16 + hashes15 + hashes14 + hashes13 + hashes12 + hashes11 + hashes10 + hashes9 + hashes8 + hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes + [h for r in archive17["lots"] for h in r["media_sha256"]]
        if (len(hashes18) != 54 or len(set(hashes18)) != 54 or set(hashes18).intersection(prior18)
                or hashlib.sha256("".join(hashes18).encode()).hexdigest() != "38400fb152f953d1f1a771ec56cef4a931e420a099c8955716161cdbf1d129ca"):
            raise RuntimeError("PAPAUTO_POLICY: 18 image/sheet originals altered or reused")
        for rec in archived18:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Цена по данным аукциона", rights_confirmed=False)
            additional.append(card)
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
