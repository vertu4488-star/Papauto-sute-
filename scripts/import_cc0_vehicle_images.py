#!/usr/bin/env python3
"""Fetch ONLY specifically approved CC0 real model photos from Wikimedia Commons.

This script is run in GitHub Actions; it saves local optimized WebP images.
The corresponding Commons file description must actually declare CC0. Sources
remain in research records; no user-facing third-party links are introduced.
"""
import hashlib
import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "research" / "approved-cc0-vehicle-sources.json"
OUT = ROOT / "assets" / "demo"
LEDGER = ROOT / "research" / "cc0-photo-provenance.json"
WIKI = "https://commons.wikimedia.org/w/api.php"
HEADERS = {
    "User-Agent": "PapAutoIllustrativeImageImporter/1.0 (https://papauto.ru/; commercial catalog photo rights audit)",
    "Accept": "application/json,image/jpeg,image/webp,image/png,*/*",
}


def main():
    entries = json.loads(SOURCES.read_text(encoding="utf-8"))["photos"]
    session = requests.Session()
    session.headers.update(HEADERS)
    OUT.mkdir(parents=True, exist_ok=True)
    old_records = {}
    if LEDGER.exists():
        for record in json.loads(LEDGER.read_text(encoding="utf-8")).get("photos", []):
            old_records[record["source_title"]] = record
    results = []
    for item in entries:
        # Skip previously verified real CC0 files when the exact photographed
        # source, file path and SHA-256 are already recorded in provenance.
        # This avoids re-downloading 300 existing photos on every extension.
        previous = old_records.get("File:" + item["commons_filename"])
        dest = OUT / item["local_name"]
        if (previous and previous.get("file") == "/assets/demo/" + dest.name
                and previous.get("rights") == "Creative Commons Zero 1.0 Universal (CC0)"
                and dest.is_file() and dest.stat().st_size > 32_000
                and hashlib.sha256(dest.read_bytes()).hexdigest() == previous.get("image_sha256")):
            results.append(previous)
            print("Previously verified CC0 image preserved:", dest.name)
            continue
        filename = item["commons_filename"]
        params = {
            "action": "query",
            "titles": "File:" + filename,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|size",
            "iiurlwidth": "1440",
            "format": "json",
            "formatversion": "2",
        }
        response = session.get(WIKI, params=params, timeout=35)
        response.raise_for_status()
        pages = response.json()["query"]["pages"]
        if not pages or not pages[0].get("imageinfo"):
            raise ValueError("No Wikimedia file information for " + filename)
        info = pages[0]["imageinfo"][0]
        meta = info.get("extmetadata") or {}
        lic = (meta.get("LicenseShortName") or {}).get("value", "")
        license_url = (meta.get("LicenseUrl") or {}).get("value", "")
        if "CC0" not in lic and "publicdomain/zero" not in license_url.lower():
            raise ValueError("Image is NOT CC0: " + filename + " license=" + lic)
        if not info.get("mime", "image/jpeg").startswith("image/"):
            raise ValueError("Not an image: " + filename)
        url = info.get("thumburl") or info["url"]
        # Wikimedia throttles automated clients; retry a small number of times.
        raw = None
        for retry in range(3):
            got = session.get(url, timeout=50, headers={"Referer": "https://commons.wikimedia.org/"})
            if got.ok and len(got.content) > 25_000:
                raw = got.content
                break
            time.sleep(2 * (retry + 1))
        if raw is None:
            raise RuntimeError("Could not retrieve approved photo " + filename)
        im = Image.open(io.BytesIO(raw))
        im = ImageOps.exif_transpose(im).convert("RGB")
        if im.width < 750 or im.height < 450:
            raise ValueError("Source image resolution too low: " + filename)
        im.thumbnail((1440, 1000), Image.Resampling.LANCZOS)
        dest = OUT / item["local_name"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        im.save(dest, "WEBP", quality=87, method=6)
        content = dest.read_bytes()
        if len(content) < 32_000:
            raise ValueError("Optimized image is suspiciously small: " + str(dest))
        results.append({
            "model": item["model"],
            "file": "/assets/demo/" + dest.name,
            "source_title": "File:" + filename,
            "source_page": "https://commons.wikimedia.org/wiki/File:" + quote(filename.replace(" ", "_")),
            "rights": "Creative Commons Zero 1.0 Universal (CC0)",
            "license_evidence": license_url,
            "author": item["author"],
            "image_sha256": hashlib.sha256(content).hexdigest(),
            "width": im.width,
            "height": im.height,
            "size_bytes": len(content),
            "verified_at_utc": datetime.now(timezone.utc).isoformat()
        })
        print(f"Imported {dest.name}: {im.width}x{im.height}, {len(content)} bytes, {lic}")
    LEDGER.write_text(json.dumps({"photos": results}, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print("All", len(results), "CC0 car photographs have been verified and self-hosted.")


if __name__ == "__main__":
    main()
