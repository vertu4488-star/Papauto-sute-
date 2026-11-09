#!/usr/bin/env python3
"""One-shot rights-audited replacement of the dirty Hyundai Tucson model photo.

Fetches the verified Wikimedia Commons photograph, writes a self-hosted WebP
and updates provenance/attribution, homepage and model directory. It never
copies a seller listing or asserts that the pictured car is a live/closed lot.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlparse

import requests
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
TITLE = "Hyundai Tucson NX4 SWB Serenity White Pearl (2).jpg"
SOURCE_TITLE = "File:" + TITLE
PAGE_URL = "https://commons.wikimedia.org/wiki/File:" + quote(TITLE.replace(" ", "_"))
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
AUTHOR = "Damian B Oh"
OLD = "/assets/demo/hyundai-tucson-cc0.webp"
NEW = "/assets/demo/hyundai-tucson-nx4-licensed.webp"
API = "https://commons.wikimedia.org/w/api.php"


def replace_exact(file: str, before: str, after: str, count: int = 1) -> None:
    dest = ROOT / file
    text = dest.read_text(encoding="utf-8")
    actual = text.count(before)
    if actual != count:
        raise RuntimeError(f"{file}: expected {count} old references, found {actual}")
    dest.write_text(text.replace(before, after), encoding="utf-8")


def main() -> None:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "PAPAUTO-LicensedImageImporter/1.0 (https://papauto.ru; image reuse audit)",
        "Accept": "application/json,image/jpeg,image/*",
    })
    params = {
        "action": "query",
        "titles": SOURCE_TITLE,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|size|mime",
        "iiurlwidth": "1280",
        "format": "json",
        "formatversion": "2",
    }
    result = s.get(API, params=params, timeout=35)
    result.raise_for_status()
    pages = result.json()["query"]["pages"]
    if not pages or "imageinfo" not in pages[0]:
        raise RuntimeError("Approved Commons file not found")
    info = pages[0]["imageinfo"][0]
    meta = info.get("extmetadata") or {}
    url = (meta.get("LicenseUrl") or {}).get("value", "")
    parsed = urlparse(url)
    if parsed.hostname not in ("creativecommons.org", "www.creativecommons.org") or \
            parsed.path.rstrip("/") != "/licenses/by-sa/4.0":
        raise RuntimeError("Unsupported or changed photo license: " + url)
    artist = (meta.get("Artist") or {}).get("value", "")
    if AUTHOR.lower() not in re.sub("<[^>]+>", " ", artist).lower():
        raise RuntimeError("Photographer attribution changed; review manually: " + artist[:150])
    if not info.get("mime", "").startswith("image/"):
        raise RuntimeError("Source is not an image")
    source_url = info.get("thumburl") or info["url"]
    raw = None
    for n in range(4):
        try:
            response = s.get(source_url, timeout=60, headers={"Referer": "https://commons.wikimedia.org/"})
            if response.ok and len(response.content) > 50000:
                raw = response.content
                break
            print("Photo HTTP status:", response.status_code, "attempt", n+1)
        except requests.RequestException as err:
            print("Photo fetch retry:", type(err).__name__)
        time.sleep(2 * (n + 1))
    if raw is None:
        raise RuntimeError("Could not download verified photo")

    with Image.open(io.BytesIO(raw)) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")
    if image.width < 900 or image.height < 650:
        raise RuntimeError("Source photo unexpectedly small")
    image.thumbnail((1280, 1000), Image.Resampling.LANCZOS)
    dest = ROOT / NEW.lstrip("/")
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest, format="WEBP", quality=86, method=6)
    bytes_ = dest.read_bytes()
    if len(bytes_) < 60000:
        raise RuntimeError("Optimized photo unexpectedly small")

    provenance = ROOT / "research/cc0-photo-provenance.json"
    data = json.loads(provenance.read_text(encoding="utf-8"))
    old_rows = [r for r in data["photos"] if r["file"] == OLD]
    if len(old_rows) != 1:
        raise RuntimeError("Expected exactly one previous Tucson photo record")
    data["photos"] = [r for r in data["photos"] if r["file"] not in (OLD, NEW)]
    data["photos"].append({
        "model": "Hyundai Tucson NX4",
        "file": NEW,
        "source_title": SOURCE_TITLE,
        "source_page": PAGE_URL,
        "rights": "CC BY-SA 4.0",
        "license_evidence": LICENSE_URL,
        "author": AUTHOR,
        "image_sha256": hashlib.sha256(bytes_).hexdigest(),
        "width": image.width,
        "height": image.height,
        "size_bytes": len(bytes_),
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    provenance.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    approved = ROOT / "research/approved-cc0-vehicle-sources.json"
    sources = json.loads(approved.read_text(encoding="utf-8"))
    matches = [r for r in sources["photos"] if r["local_name"] == OLD.rsplit("/", 1)[-1]]
    if len(matches) != 1:
        raise RuntimeError("Expected one original approved Tucson source")
    matches[0].update({"model": "Hyundai Tucson NX4",
                       "local_name": NEW.rsplit("/", 1)[-1],
                       "commons_filename": TITLE,
                       "author": AUTHOR})
    approved.write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    replace_exact("index.html", 'src="' + OLD + '"', 'src="' + NEW + '"')
    replace_exact("catalog-open-data.js", '"' + OLD + '"', '"' + NEW + '"')

    credits = ROOT / "photo-credits.html"
    html = credits.read_text(encoding="utf-8")
    if NEW in html:
        raise RuntimeError("Photo already credited; no duplicate import needed")
    entry = (
        '<li><strong>Hyundai Tucson NX4 (2023, Корея)</strong>: Damian B Oh · '
        '<a href="' + PAGE_URL + '" rel="noopener noreferrer">фотография автора</a> · '
        '<a href="' + LICENSE_URL + '" rel="noopener noreferrer">CC BY-SA 4.0</a> · '
        '<a href="' + NEW + '">локальная копия</a>. '
        '<small>Изменения: уменьшение размера и преобразование в WebP. '
        'Фотография модели, не автомобиль из объявления PapAuto.</small></li>\n'
    )
    if "<ol>" not in html:
        raise RuntimeError("Missing attribution list")
    credits.write_text(html.replace("<ol>", "<ol>\n" + entry, 1), encoding="utf-8")

    replace_exact("scripts/build_static_public.py",
                  'r"/assets/demo/[a-z0-9-]+-cc0\\.webp"',
                  'r"/assets/demo/[a-z0-9-]+-(?:cc0|licensed)\\.webp"')
    replace_exact("tests/test_visual_showroom.py",
                  'r"^/assets/demo/[a-z0-9-]+-cc0\\.webp$"',
                  'r"^/assets/demo/[a-z0-9-]+-(?:cc0|licensed)\\.webp$"')
    print(f"Imported {NEW}: {image.width}x{image.height}, {len(bytes_)} bytes, {LICENSE_URL}")
    print("Updated homepage, full directory, rights ledger, author credits and safe public build.")


if __name__ == "__main__":
    main()
