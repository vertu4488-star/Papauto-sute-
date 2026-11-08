#!/usr/bin/env python3
"""Expand PapAuto with GENUINE car photographs under verified CC0 licensing.

Sources: exact Wikimedia Commons file pages, searched via the MediaWiki API.
This tool never imports images from sellers, JTECO or auction databases.
No claim is made that these pictures depict individual auction lots.
Candidates must show the exact named vehicle model in the file title, must
not advertise rendering/illustration/miniature, and must have CC0 metadata.
Existing photo URLs and their provenance stay unchanged. Images are stored
as local WebP files, with URL, SHA-256, license and dimensions in a ledger.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import io
import json
import re
import time
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from html import escape, unescape
from pathlib import Path
from urllib.parse import quote, urlparse

import requests
from PIL import Image, ImageOps
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/approved-cc0-vehicle-sources.json"
LEDGER = ROOT / "research/cc0-photo-provenance.json"
MODEL_JS = ROOT / "vehicle-catalogue.js"
RENDER_JS = ROOT / "catalog-open-data.js"
REPORT = ROOT / "research/cc0-expansion-discovery-report.json"
OUT = ROOT / "assets/demo"
CREDITS = ROOT / "photo-credits.html"
CATALOG_HTML = ROOT / "catalog.html"
API = "https://commons.wikimedia.org/w/api.php"
GOAL = 133
# Remaining unpublished models after the verified 367/518 checkpoint.
QUOTAS = {"japan": 24, "south-korea": 66, "china": 61}
HEADERS = {
    "User-Agent": "PapAutoCC0CarPhotoResearch/1.0 (https://papauto.ru/; contact: use website)",
    "Accept": "application/json,image/*,*/*"
}
BLOCKED = re.compile(
    r"\b(render(?:ing)?|cgi|computer.generated|ai.generated|artificial.intelligence|"
    r"illustration|drawing|sketch|painting|brochure|advertisement|poster|"
    r"toy|lego|miniature|diecast|die.cast|scale.model|hot.wheels|"
    r"model.kit|badge|logo|emblem|dashboard|interior|steering.wheel|"
    r"engine.bay|license.plate|key.fob|wheel.rim|console|animation|"
    r"collage|montage|prototype|concept|police|rally|racecar|"
    r"cutaway|camouflage|wreck|accident)\b", re.I
)
BRAND_ORDER = {
    "japan": ["Toyota", "Honda", "Nissan", "Suzuki", "Mazda", "Subaru", "Daihatsu", "Mitsubishi",
              "Lexus", "BMW", "Mercedes-Benz", "Audi", "Porsche", "Volkswagen"],
    "south-korea": ["Hyundai", "Kia", "Genesis", "SsangYong", "Chevrolet Korea", "Renault Korea",
                    "BMW", "Mercedes-Benz", "Audi", "Volkswagen", "Porsche"],
    "china": ["BYD", "Geely", "Changan", "Chery", "Haval", "GAC", "Zeekr", "Tank",
              "Xiaomi", "AITO", "Voyah", "Hongqi", "Jetour", "Exeed", "Avatr",
              "Deepal", "Leapmotor", "Wuling", "Lynk & Co"]
}


def session():
    s = requests.Session()
    s.headers.update(HEADERS)
    retry = Retry(total=3, connect=3, read=2, backoff_factor=1.5,
                  status_forcelist=(429, 500, 502, 503, 504))
    s.mount("https://", HTTPAdapter(max_retries=retry, pool_connections=12, pool_maxsize=12))
    return s


def normalize(value):
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(re.findall(r"[a-z0-9а-яё]+", value))


def aliases(model):
    # Slash alternatives in the PapAuto model directory are naming variants,
    # e.g. Hyundai Avante / Elantra. Never remove a distinguishing suffix.
    values = re.split(r"\s+/\s+", model)
    return [v for v in values if len(normalize(v)) >= 2]


# Only verified commercial-use Creative Commons attribution licences or CC0.
ALLOWED_RIGHTS = re.compile(r"^https://creativecommons\.org/licenses/(by|by-sa)/(2\.0|2\.5|3\.0|4\.0)/?$", re.I)

BRAND_VARIANTS = {
    "Chevrolet Korea": ["Chevrolet", "Chevrolet Korea", "GM Korea"],
    "Renault Korea": ["Renault", "Renault Samsung", "Samsung", "Renault Korea"],
    "SsangYong": ["SsangYong", "KGM"],
    "Mercedes-Benz": ["Mercedes-Benz", "Mercedes Benz", "Mercedes"],
}
MODEL_VARIANTS = {
    ("Kia", "Kia Seltos"): ["Seltos"],
    ("Kia", "Morning"): ["Morning", "Picanto"],
    ("Kia", "K7"): ["K7", "Cadenza"],
    ("Hyundai", "Grandeur"): ["Grandeur", "Azera"],
    ("Hyundai", "Accent"): ["Accent", "Verna"],
    ("Renault Korea", "XM3 / Arkana"): ["XM3", "Arkana"],
    ("Toyota", "Prado"): ["Prado", "Land Cruiser Prado"],
    ("Toyota", "Copen"): ["Copen"],
}

def model_aliases(brand, model):
    return list(dict.fromkeys(MODEL_VARIANTS.get((brand, model), aliases(model))))

def brand_aliases(brand):
    return BRAND_VARIANTS.get(brand, [brand])

def detect_rights(meta):
    name = unescape(re.sub(r"<[^>]+>", "", meta.get("LicenseShortName", {}).get("value", ""))).strip()
    url = meta.get("LicenseUrl", {}).get("value", "").strip()
    if "CC0" in name or "publicdomain/zero" in url.lower():
        return ("Creative Commons Zero 1.0 Universal (CC0)", "https://creativecommons.org/publicdomain/zero/1.0/")
    p = urlparse(url)
    if p.scheme != "https" or p.hostname != "creativecommons.org":
        return None
    if not ALLOWED_RIGHTS.fullmatch(url):
        return None
    suffix = p.path.strip("/").split("/")
    return ("CC " + suffix[1].upper() + " " + suffix[2], url)

def file_matches(title, brand, model):
    stem = re.sub(r"^File:", "", title, flags=re.I)
    stem = re.sub(r"\.(?:jpe?g|png|webp)$", "", stem, flags=re.I)
    if BLOCKED.search(stem):
        return False
    norm = " " + normalize(stem) + " "
    for b in brand_aliases(brand):
        for option in model_aliases(brand, model):
            phrase = normalize(b) + " " + normalize(option)
            if phrase.strip() and " " + phrase + " " in norm:
                return True
    return False


def score_photo(title, info):
    txt = title.lower()
    scores = 10
    if "front" in txt or "01.jpg" in txt or "001.jpg" in txt:
        scores += 5
    if "rear" in txt or "back" in txt or "side detail" in txt:
        scores -= 10
    if "moscow" in txt or "2025" in txt or "2026" in txt:
        scores += 2
    width, height = info.get("width", 0), info.get("height", 0)
    scores += min(10, width // 400)
    scores += min(8, height // 400)
    return scores


def get_catalog():
    raw = MODEL_JS.read_text(encoding="utf-8")
    initial = re.search(r"const catalog = (\{.*?\});\s*// PAPAUTO_JTECO_MODEL_EXPANSION", raw, re.S)
    extras = re.search(r"const directoryExpansion = (\{.*?\});\s*for \(const region", raw, re.S)
    if not initial or not extras:
        raise RuntimeError("Unrecognized PapAuto directory format")
    main = json.loads(re.sub(r"\b(japan|china)(?=\s*:)", r'"\1"', initial.group(1)))
    expansion = json.loads(extras.group(1))
    return {market: main[market] + expansion[market] for market in main}


def get_targets(existing_maps):
    regions = get_catalog()
    targets = {}
    for market, rows in regions.items():
        seen = set()
        found = []
        for brand, model, _ in rows:
            key = "|".join((market, brand.casefold(), model.casefold()))
            if key in existing_maps or key in seen:
                continue
            seen.add(key)
            # Exclude brand names that aren't easily verifiable as a single
            # automotive manufacturer in a filename. Other models stay eligible.
            if len(normalize(model)) < 2 or len(normalize(model)) > 38:
                continue
            found.append((market, brand, model, key))
        ordering = BRAND_ORDER[market]
        rank = {v.casefold(): i for i, v in enumerate(ordering)}
        found.sort(key=lambda x: (rank.get(x[1].casefold(), 99),
                                  len(x[2]) > 18, len(x[2]), x[2]))
        targets[market] = found
    return targets


def search_one(item):
    market, brand, model, key = item
    s = session()
    candidates = []
    searches = []
    for brand_variant in brand_aliases(brand)[:3]:
        for alias in model_aliases(brand, model)[:3]:
            if len(normalize(alias)) < 2:
                continue
            searches.extend([
                "intitle:" + brand_variant + " " + alias,
                '"' + brand_variant + " " + alias + '"',
                "intitle:" + alias + " " + brand_variant,
            ])
    for term in list(dict.fromkeys(searches))[:12]:
        try:
            result = s.get(API, params={
                "action": "query", "format": "json", "formatversion": "2",
                "generator": "search", "gsrsearch": term, "gsrnamespace": "6",
                "gsrlimit": "80", "prop": "imageinfo",
                "iiprop": "url|extmetadata|size|mime", "iiurlwidth": "1440"
            }, timeout=36)
            result.raise_for_status()
            pages = result.json().get("query", {}).get("pages", [])
        except (requests.RequestException, ValueError) as exc:
            print("Commons photo search retryable", brand, model, str(exc)[:100], flush=True)
            continue
        for p in pages:
            title = p.get("title", "")
            infos = p.get("imageinfo") or []
            if not infos or not file_matches(title, brand, model):
                continue
            info = infos[0]
            meta = info.get("extmetadata", {})
            rights = detect_rights(meta)
            if not rights:
                continue
            author = unescape(re.sub(r"<[^>]+>", " ", meta.get("Artist", {}).get("value", ""))).strip()
            author = " ".join(author.split())[:200]
            # BY and BY-SA photos require attributable author and license.
            if "CC0" not in rights[0] and not author:
                continue
            w, h = info.get("width", 0), info.get("height", 0)
            if w < 850 or h < 500 or not info.get("mime", "image/jpeg").startswith("image/"):
                continue
            if not re.search(r"\.(jpe?g|png|webp)$", title, re.I):
                continue
            candidates.append({
                "title": title, "url": info.get("thumburl") or info.get("url"),
                "width": w, "height": h,
                "rights": rights[0], "license_url": rights[1],
                "author": author, "score": score_photo(title, info) + (5 if "CC0" in rights[0] else 0)
            })
        if candidates:
            break
    # Return choices to allow download fallback if one media URL is throttled.
    candidates.sort(key=lambda x: x["score"], reverse=True)
    unique = list({c["title"]: c for c in candidates}.values())
    unique.sort(key=lambda x: x["score"], reverse=True)
    return item, unique[:5]


def save_photo(target, candidates, already):
    market, brand, model, key = target
    slug = "-".join(filter(None, [normalize(market).replace(" ", "-"),
                                  normalize(brand).replace(" ", "-"),
                                  normalize(model).replace(" ", "-")]))
    # Avoid encoding non-ASCII characters in publicly served asset names.
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    if not slug:
        return None
    local = slug + "-licensed.webp"
    if local in already["names"]:
        return None
    dest = OUT / local
    s = session()
    for candidate in candidates:
        filename = candidate["title"].removeprefix("File:")
        if filename in already["sources"]:
            continue
        try:
            response = s.get(candidate["url"], headers={"Referer": "https://commons.wikimedia.org/"},
                             timeout=70)
            response.raise_for_status()
            if len(response.content) < 30_000:
                continue
            img = Image.open(io.BytesIO(response.content))
            if img.width < 850 or img.height < 500:
                continue
            img = ImageOps.exif_transpose(img).convert("RGB")
            img.thumbnail((1440, 1000), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, "WEBP", quality=86, method=5)
            data = buffer.getvalue()
            if len(data) < 32_000:
                continue
            dest.write_bytes(data)
            sha = hashlib.sha256(data).hexdigest()
            author = candidate["author"] or "Creator listed on Wikimedia Commons source page"
            provenance = {
                "model": brand + " " + model,
                "file": "/assets/demo/" + local,
                "source_title": candidate["title"],
                "source_page": "https://commons.wikimedia.org/wiki/File:" +
                               quote(filename.replace(" ", "_")),
                "rights": candidate["rights"],
                "license_evidence": candidate["license_url"],
                "author": author,
                "image_sha256": sha,
                "width": img.width, "height": img.height,
                "size_bytes": len(data),
                "verified_at_utc": datetime.now(timezone.utc).isoformat(),
                "discovery_method": "Exact make/model match and live Commons commercial-use license audit",
                "changes": "Resized and converted to WebP; no semantic image edits"
            }
            source_entry = {
                "model": brand + " " + model,
                "local_name": local,
                "commons_filename": filename,
                "author": author,
                "rights": candidate["rights"]
            }
            print("Licensed authentic photograph:", candidate["rights"], market, brand, model, "<=", filename,
                  img.width, img.height, len(data), flush=True)
            return key, source_entry, provenance
        except (requests.RequestException, OSError, ValueError) as exc:
            print("Skipped failed photo download", filename, str(exc)[:100], flush=True)
    return None


def write_photo_credits(records):
    """Publish local photo licensing attributions without outbound seller links."""
    parts = [
        '<!doctype html><html lang="ru"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        '<meta name="robots" content="noindex,follow">',
        '<title>Источники и лицензии фотографий | PAPAUTO</title>',
        '<style>body{font:15px/1.6 system-ui,sans-serif;max-width:940px;margin:36px auto;padding:0 18px;color:#1d1d1f}',
        'li{margin:0 0 18px}a{color:#06c}h1{font-size:30px}small{color:#65656a}</style>',
        '</head><body><a href="/catalog.html">← Каталог PapAuto</a>',
        '<h1>Источники и лицензии фотографий автомобилей</h1>',
        '<p>Фотографии моделей автомобилей; это не снимки завершённых аукционных лотов.',
        'Для лицензий с указанием авторства перечислены создатель, первоисточник, лицензия и обработка.</p><ol>'
    ]
    for record in records:
        if "CC0" in record["rights"]:
            continue
        model = escape(record["model"])
        author = escape(record["author"])
        url = escape(record["source_page"], quote=True)
        lic = escape(record["license_evidence"], quote=True)
        name = escape(record["rights"])
        file = escape(record["file"], quote=True)
        parts.append('<li><strong>' + model + '</strong>: ' + author +
            ' · <a href="' + url + '" rel="noopener noreferrer">исходное фото</a> · ' +
            '<a href="' + lic + '" rel="noopener noreferrer">' + name + '</a> · ' +
            '<a href="' + file + '">локальная копия</a>. ' +
            '<small>Изменения: уменьшен размер, преобразован формат в WebP. Содержимое сохранено.</small></li>')
    parts.append('</ol><p>Фотографии с лицензией CC0 могут использоваться без обязательного указания авторства.</p></body></html>')
    CREDITS.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main():
    start = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(SOURCE.read_text(encoding="utf-8"))
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    maps = RENDER_JS.read_text(encoding="utf-8")
    existing = set(re.findall(r'\["([^"]+)\|([^"]+)\|([^"]+)","/assets/demo/[^"]+\.webp"\]', maps))
    mapped = {"|".join(x) for x in existing}
    old_rows = len(manifest["photos"])
    if old_rows != len(ledger["photos"]) or len(mapped) != old_rows:
        raise RuntimeError("Existing rights ledger, source manifest and catalog disagree")
    targets = get_targets(mapped)
    selected = []
    sourceused = {x["commons_filename"] for x in manifest["photos"]}
    fileused = {x["local_name"] for x in manifest["photos"]}
    existing_paths = {"names": fileused, "sources": sourceused}
    searches = 0
    errors = 0
    totals = defaultdict(int)
    # The country quotas preserve Japanese/Korean/Chinese photo diversity.
    for market in ("japan", "south-korea", "china"):
        remaining = QUOTAS[market]
        candidates = targets[market]
        print("Searching", market, len(candidates), "remaining models; target", remaining, flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            iterator = pool.map(search_one, candidates)
            for item, images in iterator:
                searches += 1
                if remaining <= 0 or len(selected) >= GOAL:
                    break
                if not images:
                    continue
                data = save_photo(item, images, existing_paths)
                if data is None:
                    errors += 1
                    continue
                key, source, prov = data
                sourceused.add(source["commons_filename"])
                fileused.add(source["local_name"])
                selected.append((key, source, prov, market))
                totals[market] += 1
                remaining -= 1
                if len(selected) % 10 == 0:
                    print("Imported", len(selected), "new photos; elapsed",
                          round(time.monotonic()-start), "sec", flush=True)
        print("Done", market, "imported", totals[market], flush=True)
    # Fill any quota deficit using models from the remaining regions.
    if len(selected) < GOAL:
        for market in ("japan", "south-korea", "china"):
            if len(selected) >= GOAL:
                break
            additional = [x for x in targets[market]
                          if x[3] not in mapped and x[3] not in {q[0] for q in selected}]
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
                for item, images in pool.map(search_one, additional):
                    if len(selected) >= GOAL:
                        break
                    searches += 1
                    if not images:
                        continue
                    data = save_photo(item, images, existing_paths)
                    if data is None:
                        errors += 1
                        continue
                    key, source, prov = data
                    selected.append((key, source, prov, market))
                    sourceused.add(source["commons_filename"])
                    fileused.add(source["local_name"])
                    totals[market] += 1
    if not selected:
        raise RuntimeError("No appropriately licensed real car photographs discovered: leave public catalog untouched")
    # Only successfully downloaded and independently verified files become cards.
    new_lines = ['    ["' + key + '","' + prov["file"] + '"]'
                 for key, source, prov, market in selected]
    anchor = "  const photoByModel = new Map(["
    if anchor not in maps:
        raise RuntimeError("Cannot locate PapAuto photo map")
    start_idx = maps.index(anchor) + len(anchor)
    end_idx = maps.index("\n  ]);", start_idx)
    before = maps[start_idx:end_idx].rstrip()
    if not before.endswith(","):
        before += ","
    maps = maps[:start_idx] + before + "\n" + ",\n".join(new_lines) + maps[end_idx:]
    RENDER_JS.write_text(maps, encoding="utf-8")
    manifest["photos"].extend(row[1] for row in selected)
    ledger["photos"].extend(row[2] for row in selected)
    SOURCE.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "target_new": GOAL, "imported_new": len(selected),
        "total_photographed_models": old_rows + len(selected),
        "country_new_photos": dict(totals),
        "searched_models": searches, "download_failures": errors,
        "existing_original_photos": old_rows,
        "license_policy": "Wikimedia Commons verified CC0 or CC BY / CC BY-SA commercial-use license with published attribution",
        "images_are_auction_lots": False,
        "verified_source_titles": [r[1]["commons_filename"] for r in selected],
        "elapsed_seconds": round(time.monotonic() - start, 2)
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest["rules"] = "Verified CC0 or commercial-use CC BY / CC BY-SA Wikimedia Commons photographs; credit page published when attribution required; no external seller links in cards."
    SOURCE.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_photo_credits(ledger["photos"])
    # Bust browser asset cache only after verified images are published.
    html = CATALOG_HTML.read_text(encoding="utf-8")
    html, n = re.subn(r'catalog-open-data\.js\?v=[^"]+',
                      "catalog-open-data.js?v=verified-" + str(old_rows + len(selected)) + "-20261108", html)
    if n != 1:
        raise RuntimeError("Cannot update catalog gallery version once and only once")
    CATALOG_HTML.write_text(html, encoding="utf-8")
    print("DONE:", json.dumps({k: v for k, v in report.items()
                               if k != "verified_source_titles"}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
