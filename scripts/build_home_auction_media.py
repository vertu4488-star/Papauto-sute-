"""Build locally hosted, exact-lot auction galleries with fail-closed main media.

Each lot must have its genuine auction photograph and sheet. Optional extra
angles that the source reports as GIF placeholders are removed, not shown.
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
JPEG_MAGIC = bytes.fromhex("ffd8ff")

def download_one(pair):
    rel, url, required = pair
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != HOST or not parsed.path.startswith("/imgs/") or parsed.query:
        raise RuntimeError("Unexpected auction image source for " + str(rel))
    for attempt in range(3 if required else 2):
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
            if 3_000 <= len(payload) <= 4_000_000 and payload[:3] == JPEG_MAGIC:
                return rel, payload
            if not required:
                print("Omitting non-JPEG optional auction angle " + str(rel) + " (" + str(len(payload)) + " bytes)")
                return rel, None
            raise RuntimeError("Required auction JPEG missing: " + str(rel) + " " + payload[:18].hex())
        except Exception:
            if attempt == (2 if required else 1):
                if not required:
                    print("Omitting unavailable optional auction angle " + str(rel))
                    return rel, None
                raise
            time.sleep(attempt + 1)
    raise RuntimeError("Could not fetch required media " + str(rel))

def materialize(root):
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    lots = doc.get("records", [])
    if len(lots) != 25:
        raise RuntimeError("Expected 25 exact auction lots")
    tasks = []
    for lot in lots:
        slug = lot["slug"]
        if not SLUG_RE.fullmatch(slug):
            raise RuntimeError("Invalid lot slug")
        photos = lot.get("auction_photos", [])
        if not (2 <= len(photos) <= 3):
            raise RuntimeError("Missing original auction gallery for " + slug)
        if photos[0] != lot["cover_photo_reference"]:
            raise RuntimeError("Cover photo mismatched to lot " + slug)
        for index, url in enumerate(photos, 1):
            tasks.append((ASSET_DIR / (slug + "-photo-" + str(index) + ".jpg"), url, index == 1))
        tasks.append((ASSET_DIR / (slug + "-sheet.jpg"), lot["auction_sheet_reference"], True))
    if len({str(rel) for rel, url, required in tasks}) != len(tasks):
        raise RuntimeError("Duplicate media names")
    downloaded, skipped = {}, []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(download_one, pair) for pair in tasks]
        for f in as_completed(futures):
            rel, data = f.result()
            if data is None:
                skipped.append(rel)
            else:
                downloaded[rel] = data
    for rel, data in downloaded.items():
        dest = Path(root) / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    # Missing optional angles must not leave broken thumbnails on either page.
    if skipped:
        for name in ("index.html", "auction-lots.html"):
            page = Path(root) / name
            html = page.read_text(encoding="utf-8")
            for rel in skipped:
                url = "/" + rel.as_posix()
                pattern = r'<a href="' + re.escape(url) + r'"[^>]*>.*?</a>'
                html, count = re.subn(pattern, "", html, count=1, flags=re.S)
                if name == "auction-lots.html" and count != 1:
                    raise RuntimeError("Gallery thumbnail was not removed: " + url)
            page.write_text(html, encoding="utf-8")
    required_count = sum(1 for _, _, required in tasks if required)
    if required_count != 2 * len(lots) or len(downloaded) < required_count:
        raise RuntimeError("One or more required auction main photos or sheets not present")
    print(f"Prepared {len(downloaded)} local auction JPEG files; omitted {len(skipped)} unavailable angles")
    return len(downloaded)

if __name__ == "__main__":
    materialize(ROOT / "render-public")
