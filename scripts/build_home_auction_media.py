"""Materialize exact-lot auction gallery media into the PapAuto static output.
All source references are pinned in GitHub research JSON. No browser hotlinks.
Build refuses to deploy if an image is unavailable or invalid.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json
import re
import time
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research" / "home-8-exact-lot-photo-sheet-references-2026-11-12.json"
ASSET_DIR = Path("assets/auction/home")
SLUG_RE = re.compile(r"^[a-z0-9-]+$")
HOST = "7.tru.ru"

def download_one(pair):
    rel, url = pair
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != HOST or not parsed.path.startswith("/imgs/") or parsed.query:
        raise RuntimeError("Unexpected auction image source for " + str(rel))
    payload = None
    for attempt in range(3):
        try:
            request = Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; PapAuto/1.0)",
                "Accept": "image/jpeg,image/*;q=0.9",
                "Referer": "https://atp-auto.ru/",
            })
            with urlopen(request, timeout=22) as response:
                payload = response.read(4_000_001)
                if response.status != 200:
                    raise RuntimeError("Unexpected response status")
            if 3_000 <= len(payload) <= 4_000_000 and payload[:3] == bytes.fromhex("ffd8ff"):
                return rel, payload
            raise RuntimeError("Invalid JPEG " + str(rel) + " from " + urlsplit(url).path + ": bytes=" + str(len(payload)) + ", magic=" + payload[:18].hex() + ", type=" + str(response.headers.get("Content-Type")))
        except Exception:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)
    raise RuntimeError("Could not fetch " + str(rel))

def materialize(root):
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    lots = doc.get("records", [])
    if len(lots) != 8:
        raise RuntimeError("Expected eight exact auction lots")
    tasks = []
    for lot in lots:
        slug = lot["slug"]
        if not SLUG_RE.fullmatch(slug):
            raise RuntimeError("Invalid lot slug")
        photos = lot.get("auction_photos", [])
        if not (2 <= len(photos) <= 3):
            raise RuntimeError("Missing multiple original auction photos for " + slug)
        if photos[0] != lot["cover_photo_reference"]:
            raise RuntimeError("Cover photo mismatched to lot " + slug)
        for index, url in enumerate(photos, 1):
            tasks.append((ASSET_DIR / (slug + "-photo-" + str(index) + ".jpg"), url))
        tasks.append((ASSET_DIR / (slug + "-sheet.jpg"), lot["auction_sheet_reference"]))
    if len({str(rel) for rel, url in tasks}) != len(tasks):
        raise RuntimeError("Duplicate media names")
    # Download everything before publishing anything, to avoid incomplete cards.
    downloaded = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(download_one, pair) for pair in tasks]
        for f in as_completed(futures):
            rel, data = f.result()
            downloaded[rel] = data
    for rel, data in downloaded.items():
        dest = Path(root) / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    print(f"Prepared {len(downloaded)} verified local auction JPEG images for {len(lots)} exact lots")
    return len(downloaded)

if __name__ == "__main__":
    materialize(ROOT / "render-public")
