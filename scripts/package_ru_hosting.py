#!/usr/bin/env python3
"""Produce a clean, static Apache/REG.RU upload folder from build_static_public.py.

The Render static publisher intentionally outputs 404 tombstones to overwrite
formerly cached unwanted photos. These tombstones and developer/source files
must NOT be uploaded to a fresh Russian host. This creates an isolated
customer-site-only copy; it never changes DNS or the live Render site.
"""
from __future__ import annotations
import argparse
import json
import shutil
from pathlib import Path

TOMBSTONE = b"404 Not Found - PAPAUTO\n"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".svg", ".ico", ".woff2"}
ROOT_EXT = {".html", ".css", ".js", ".xml", ".txt"}
RETIRED_PREFIXES = (
    "assets/demo/", "assets/visual/", "assets/auction/demo-cars-sprite.webp",
    "assets/premium-auctions/audi-q2-2021-",
    "assets/premium-auctions/audi-q3-2021-",
)
# Historical street-photo lots remain only in internal source control, not in
# a fresh RU-hosting upload. Unlike an existing host/CDN, new hosting needs
# neither their retirement pages nor their placeholder photographs.
RETIRED_LOT_PAGES = frozenset({
    "lots/nissan-note-2021-227.html",
    "lots/mercedes-a180-2020.html",
})

HTACCESS = """# PapAuto for REG.RU Apache/Linux only.
# Provision valid TLS/SSL before routing papauto.ru here.
# This package does not migrate the API, Neon or Telegram.
Options -Indexes
DirectoryIndex index.html
ErrorDocument 404 /404.html

<IfModule mod_rewrite.c>
RewriteEngine On
RewriteCond %{HTTP_HOST} ^www\\.papauto\\.ru$ [NC]
RewriteRule ^(.*)$ https://papauto.ru/$1 [R=301,L,NE]
</IfModule>

<IfModule mod_deflate.c>
AddOutputFilterByType DEFLATE text/html text/plain text/css text/javascript application/javascript application/json application/xml image/svg+xml
</IfModule>

<IfModule mod_expires.c>
ExpiresActive On
ExpiresByType text/html "access plus 5 minutes"
ExpiresByType text/css "access plus 1 hour"
ExpiresByType application/javascript "access plus 1 hour"
ExpiresByType image/jpeg "access plus 1 day"
ExpiresByType image/png "access plus 1 day"
ExpiresByType image/webp "access plus 1 day"
ExpiresByType image/svg+xml "access plus 1 day"
ExpiresByType font/woff2 "access plus 7 days"
</IfModule>

<IfModule mod_headers.c>
Header always set X-Content-Type-Options "nosniff"
Header always set X-Frame-Options "DENY"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
</IfModule>

<FilesMatch "(?i)\\.(?:py|sql|env|md|yaml|yml|toml|bak|log)$">
Require all denied
</FilesMatch>
"""

def is_public(name: str, size: int) -> bool:
    if size == 0 or name.startswith(".") or ".." in Path(name).parts:
        return False
    if name in RETIRED_LOT_PAGES or any(name.startswith(prefix) for prefix in RETIRED_PREFIXES):
        return False
    parts = Path(name).parts
    if len(parts) == 1:
        return Path(name).suffix.lower() in ROOT_EXT
    if parts[0] == "data":
        return Path(name).suffix.lower() == ".json"
    if parts[0] == "lots" and len(parts) == 2:
        return Path(name).suffix.lower() == ".html"

    if parts[0] == "vendor":
        return Path(name).suffix.lower() in {".js", ".css", ".woff2"}
    if parts[0] == "assets":
        if name in {"assets/favicon.svg", "assets/papauto-logo.svg"}:
            return True
        if len(parts) >= 3 and parts[1] == "auction" and parts[2] in {"home", "approved"}:
            return Path(name).suffix.lower() in IMAGE_EXT
        if parts[1] in {"premium-auctions", "fonts"}:
            return Path(name).suffix.lower() in IMAGE_EXT
    return False

def build(source: Path, target: Path) -> dict:
    if not source.is_dir():
        raise RuntimeError("Missing source export folder: " + str(source))
    if target.resolve() == source.resolve():
        raise RuntimeError("Release target must be separate from the Render build")
    if target.exists():
        raise RuntimeError("Refusing to overwrite existing RU release: " + str(target))
    count = 0
    skipped = 0
    for item in sorted(source.rglob("*")):
        if not item.is_file():
            continue
        if item.is_symlink():
            raise RuntimeError("Source export contains a symlink: " + str(item))
        name = item.relative_to(source).as_posix()
        data = item.read_bytes()
        if data == TOMBSTONE or not is_public(name, len(data)):
            skipped += 1
            continue
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        count += 1
    required = {"index.html", "gallery.html", "gallery.js", "gallery.css",
                "podbor.html", "404.html", "robots.txt", "sitemap.xml",
                "site-config.js", "data/gallery-lots.json",
                "lots/toyota-corolla-sport-2023-20038.html",
                "assets/favicon.svg", "assets/papauto-logo.svg"}
    missing = [p for p in sorted(required) if not (target / p).is_file()]
    if missing:
        raise RuntimeError("Incomplete RU static export: " + ", ".join(missing))
    gallery = json.loads((target / "data/gallery-lots.json").read_text(encoding="utf-8"))
    lots = gallery.get("lots", [])
    if not 35 <= len(lots) <= 500 or gallery.get("lot_count") != len(lots):
        raise RuntimeError("Invalid count in full-sheet auction gallery")
    html = (target / "gallery.html").read_text(encoding="utf-8")
    if any(lot.get("id") in {
            "nissan-note-2021-227", "mercedes-a180-2020"} for lot in lots):
        raise RuntimeError("Outdoor-only lot cannot enter RU hosting export")
    if any(name in html for name in ("nissan-note-2021-227",
                                    "mercedes-a180-2020")):
        raise RuntimeError("Withdrawn auction card still present in RU gallery")
    if html.count('class="gallery-card"') != len(lots):
        raise RuntimeError("Published auction cards and data do not match")
    if len(list((target / "lots").glob("*.html"))) != len(lots):
        raise RuntimeError("RU export missing auction-lot details")
    for lot in lots:
        if lot.get("inspection_kind") != "Аукционный лист":
            raise RuntimeError("Full auction sheet missing: " + lot["id"])
        for link in [*lot["photos"], lot["inspection_image"]]:
            if not isinstance(link, str) or not link.startswith("/assets/"):
                raise RuntimeError("External photo forbidden: " + str(link))
            image = target / link.lstrip("/")
            if not image.is_file() or image.stat().st_size <= len(TOMBSTONE):
                raise RuntimeError("Auction photo/sheet missing: " + link)
    (target / ".htaccess").write_text(HTACCESS, encoding="utf-8")
    if (target / "api.py").exists() or (target / "research").exists() or (target / "assets/demo").exists():
        raise RuntimeError("Protected files or retired street photos leaked")
    result = {"published_lots": len(lots), "static_files": count + 1,
              "skipped_old_or_protected": skipped, "needs_ru_hosting_and_ssl": True}
    print("PAPAUTO_RU_CLEAN_RELEASE=" + json.dumps(result, ensure_ascii=False))
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="render-public")
    parser.add_argument("--out", default="ru-hosting-clean")
    args = parser.parse_args()
    build(Path(args.source), Path(args.out))
