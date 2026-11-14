"""Build a strict, public-only directory for the PAPAUTO Render static site.

Only whitelisted public assets are copied. Never publish the repository root:
it also contains Python API code, tests, GitHub workflows and build scripts.
Run from the repository checkout with Python 3.11+.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import re
import json

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "render-public"
ROOT_SUFFIXES = {".html", ".css", ".js", ".xml", ".webmanifest"}
# Only explicitly allowed domain-verification text files may be published; others remain tombstoned.
PUBLIC_TEXT_FILES = {"robots.txt", "ads.txt", "security.txt", "d260ebec4a8764da2a8a41fc9d6791a8.txt", "ae47dec4705c4a088f3dd56a3fdeb764.txt"}
# Some former Render builds published the whole repository. Explicit tombstones
# replace old assets that otherwise remain fetchable at their old URLs.
TOMBSTONE = b"404 Not Found - PAPAUTO\n"
PROTECTED_SUFFIXES = {".py", ".pyc", ".md", ".toml", ".yaml", ".yml", ".ini", ".cfg", ".sh", ".sql", ".log", ".lock", ".txt"}
PROTECTED_NAMES = {".gitignore", ".python-version", "Dockerfile", "Makefile", "LICENSE", "render.yaml"}
PROTECTED_DIRS = {".github", "scripts", "tests", "research", "content", "docs"}
WALK_EXCLUDE = {".git", "render-public", "node_modules", "__pycache__", ".pytest_cache", ".venv", "venv", ".mypy_cache", ".ruff_cache"}
PUBLIC_FOLDERS = {
    "assets": {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".woff2"},
    "data": {".json"},
}

# Rejected as outdoor/dealer-style presentation images. An AUCNET label in the
# frame does not certify an auction-house photograph. Never expose these bytes
# in a demo, public gallery, image URL, or future static release.
QUARANTINED_OUTDOOR_MEDIA = {
    "assets/premium-auctions/audi-q2-2021-front.webp",
    "assets/premium-auctions/audi-q2-2021-rear.webp",
    "assets/premium-auctions/audi-q2-2021-diagram.webp",
    "assets/premium-auctions/audi-q3-2021-front.webp",
    "assets/premium-auctions/audi-q3-2021-rear.webp",
    "assets/premium-auctions/audi-q3-2021-diagram.webp",
    # Visual audit 2026-11-13: open-air street/dealer/parking imagery.
    "assets/auction/home/nissan-note-2021-227-photo-1.jpg",
    "assets/premium-auctions/mercedes-a180-2020-front.webp",
    "assets/premium-auctions/mercedes-a180-2020-rear.webp",
}


def copy_public_files() -> list[str]:
    # Build gate: refuse publication when customer navigation leaves PAPAUTO.
    subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests",
         "-p", "test_no_external_sales_links.py"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests",
         "-p", "test_auction_media_policy.py"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests",
         "-p", "test_market_model_directory.py"],
        cwd=ROOT,
        check=True,
    )
    # This is a generated output directory; never accept a symbolic-link target.
    if TARGET.is_symlink():
        raise RuntimeError("Refusing to overwrite a symlinked publish directory")
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(mode=0o755)
    copied = []

    for src in sorted(ROOT.iterdir()):
        if src.is_file() and not src.is_symlink() and (src.suffix.lower() in ROOT_SUFFIXES or src.name in PUBLIC_TEXT_FILES):
            dst = TARGET / src.name
            shutil.copy2(src, dst)
            copied.append(dst.relative_to(TARGET).as_posix())

    for folder, allowed_suffixes in PUBLIC_FOLDERS.items():
        base = ROOT / folder
        if not base.is_dir() or base.is_symlink():
            continue
        for src in sorted(base.rglob("*")):
            if not src.is_file() or src.is_symlink() or src.suffix.lower() not in allowed_suffixes:
                continue
            relative = src.relative_to(ROOT)
            if relative.as_posix() in QUARANTINED_OUTDOOR_MEDIA:
                continue
            # User-selected Thursday showroom ARTWORK: one explicitly allowed advertising visual,
            # never a real auction photo and never an image for a customer lot card.
            if folder == 'assets' and (relative.parts[:2] == ('assets','demo') or (relative.parts[:2] == ('assets','visual') and relative.as_posix() not in {'assets/visual/fallback-vehicle.svg', 'assets/visual/papauto-thursday-approved-editorial-artwork-20261112.webp'})):
                continue
            dst = TARGET / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(dst.relative_to(TARGET).as_posix())

    # Explicit invalid-byte replacements for old non-auction photo URLs.
    # Render/CDN may keep deleted assets reachable after a normal static deploy.
    # Retaining ONLY tombstone pathnames prevents any original image bytes returning.
    retired_manifest = ROOT / "research" / "retired-non-auction-photo-paths-2026-11-12.json"
    retired_data = json.loads(retired_manifest.read_text(encoding="utf-8"))
    retired_media = retired_data["paths"]
    if len(retired_media) < 519 or len(set(retired_media)) != len(retired_media):
        raise RuntimeError("PAPAUTO_POLICY: expected complete unique retired-photo tombstones")
    for rel in retired_media:
        if not isinstance(rel, str) or not re.fullmatch(r"assets/[a-z0-9_./-]+", rel):
            raise RuntimeError("PAPAUTO_POLICY: invalid retired media pathname")
        if not (rel.startswith("assets/demo/")
                or rel.startswith("assets/visual/")
                or rel.startswith("assets/premium-auctions/")
                or rel == "assets/auction/demo-cars-sprite.webp"):
            raise RuntimeError("PAPAUTO_POLICY: unexpected tombstone target " + rel)
        if (ROOT / rel).exists():
            raise RuntimeError("PAPAUTO_POLICY: deleted non-auction image was restored " + rel)
        dst = TARGET / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(TOMBSTONE)
        copied.append(rel)

    # Also overwrite old direct URLs for the explicitly rejected 2021 Audi
    # photos/diagrams. They remain in source for provenance only, NOT public.
    for rel in sorted(QUARANTINED_OUTDOOR_MEDIA):
        dst = TARGET / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(TOMBSTONE)
        copied.append(rel)

    # A customer-facing complete auction card must always have the ORIGINAL
    # full auction sheet. Two 2021 Audi examples with only damage diagrams were
    # quarantined; block any accidental resurrection in the public release.
    gallery_source = json.loads((ROOT / "data" / "gallery-lots.json").read_text(encoding="utf-8"))
    complete_lots = gallery_source.get("lots", [])
    if len(complete_lots) < 37 or any(
            lot.get("inspection_kind") != "Аукционный лист" for lot in complete_lots):
        raise RuntimeError("PAPAUTO_POLICY: non-full-sheet gallery lot or incomplete baseline")
    premium_source = json.loads((ROOT / "data" / "premium-real-auction-lots.json").read_text(encoding="utf-8"))
    premium_lots = premium_source.get("lots", [])
    if len(premium_lots) != 12 or any(
            lot.get("inspection_kind") != "Аукционный лист" for lot in premium_lots):
        raise RuntimeError("PAPAUTO_POLICY: premium page must use 12 true-sheet examples")
    for page_name in ("gallery.html", "premium-japan-korea.html",
                      "premium-mobile-photo-demo.html"):
        page_text = (ROOT / page_name).read_text(encoding="utf-8")
        if ("audi-q2-2021-diagram.webp" in page_text
                or "audi-q3-2021-diagram.webp" in page_text):
            raise RuntimeError("PAPAUTO_POLICY: diagram-only Audi restored to " + page_name)

    # Download genuine exact-lot photos and sheets to our own static host.
    from build_home_auction_media import materialize
    media_count = materialize(TARGET)
    # The image materializer may re-copy pinned historical files. Replace
    # quarantined paths AFTER materialization too, preventing stale CDN bytes.
    for rejected in QUARANTINED_OUTDOOR_MEDIA:
        dst = TARGET / rejected
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(TOMBSTONE)
    if media_count != 50:
        raise RuntimeError("Expected exactly 25 screened auction covers and 25 matching sheets; unreviewed optional media blocked")

    # Expand the site from 39 baseline lots to a maximum of 500 fully approved lots.
    # Every new photo and sheet is local, licensed and matched to an auction lot.
    from compile_auction_gallery import compile_published_gallery
    gallery_result = compile_published_gallery(TARGET)
    # Final release guard: a test-only fix must never be the sole protection.
    # Quarantined source lot IDs may survive in GitHub for provenance but
    # must not be exposed in buyer-facing HTML, JSON, or full-detail pages.
    published_registry = json.loads(
        (TARGET / "data/gallery-lots.json").read_text(encoding="utf-8")
    )
    withdrawn_ids = {"nissan-note-2021-227", "mercedes-a180-2020"}
    public_ids = {lot["id"] for lot in published_registry["lots"]}
    if (published_registry["lot_count"] != gallery_result["count"]
            or published_registry["lot_count"] < 35
            or public_ids.intersection(withdrawn_ids)):
        raise RuntimeError("PAPAUTO_POLICY: quarantined outdoor lot in release")
    if gallery_result.get("detail_pages") != published_registry["lot_count"]:
        raise RuntimeError("PAPAUTO_POLICY: published detail pages mismatch gallery")
    for public_lot in published_registry["lots"]:
        detail = TARGET / "lots" / (public_lot["id"] + ".html")
        if not detail.is_file():
            raise RuntimeError("PAPAUTO_POLICY: missing buyer lot page " + public_lot["id"])
    customer_gallery = (TARGET / "gallery.html").read_text(encoding="utf-8")
    if any(id_ in customer_gallery for id_ in withdrawn_ids):
        raise RuntimeError("PAPAUTO_POLICY: outdoor lot leaked into gallery HTML")
    for photo_path in QUARANTINED_OUTDOOR_MEDIA:
        if (TARGET / photo_path).read_bytes() != TOMBSTONE:
            raise RuntimeError("PAPAUTO_POLICY: outdoor photo bytes in release")
    # Retire historical detail URL for each publicly rejected outdoor lot.
    # Preserve source evidence in GitHub, not on customer-facing pages.
    retired_lot_html = (
        '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
        '<meta name="robots" content="noindex,nofollow">'
        '<title>Лот снят с публикации | PAPAUTO</title></head>'
        '<body><main><h1>Лот снят с публикации</h1>'
        '<p>Фотографии требуют проверки. Подберите аналогичный автомобиль.</p>'
        '<a href="/gallery.html">Аукционный каталог</a></main></body></html>'
    )
    for rejected_id in ("nissan-note-2021-227", "mercedes-a180-2020"):
        retired_file = TARGET / "lots" / (rejected_id + ".html")
        retired_file.parent.mkdir(parents=True, exist_ok=True)
        retired_file.write_text(retired_lot_html, encoding="utf-8")
    print(f"Gallery published: {gallery_result['count']} exact lots; "
          f"new: {gallery_result['new']}; "
          f"omitted {gallery_result['skipped_optional']} missing optional angles")

    # The complete prebuilt SurveyJS renderer is pinned and hosted on PAPAUTO.
    # Never rely on external CDN scripts at runtime, including in Russia.
    from vendor_surveyjs import fetch_surveyjs
    fetch_surveyjs(TARGET)

    # Auction photography ONLY. Street/model photo libraries have been retired.
    forbidden_gallery = ROOT / "assets" / "demo"
    if forbidden_gallery.exists() and any(forbidden_gallery.iterdir()):
        raise RuntimeError("PAPAUTO_POLICY: assets/demo street photo gallery must never be published")
    # The source importer itself must not return in the active repository.
    if (ROOT / "research" / "cc0-photo-provenance.json").exists():
        raise RuntimeError("PAPAUTO_POLICY: obsolete street-photo source registry restored")
    # Strip external/unknown photos from old SEO and archive pages.
    for page in TARGET.glob("*.html"):
        html = page.read_text(encoding="utf-8")
        # A deleted photo must not leave an empty clickable article behind.
        # Keep the original records in GitHub; remove only the customer view.
        needs_card_removal = {
            "index.html", "auction-lots.html",
            "premium-japan-korea.html", "premium-mobile-photo-demo.html",
        }
        if page.name in needs_card_removal:
            removed = []
            def screen_article(match):
                article = match.group(0)
                if ("nissan-note-2021-227" in article or
                        "mercedes-a180-2020-front.webp" in article):
                    removed.append(article)
                    return ""
                return article
            html = re.sub(r"<article\b[^>]*>[\s\S]*?</article>\s*",
                          screen_article, html)
            if len(removed) != 1:
                raise RuntimeError(
                    "PAPAUTO_POLICY: unexpected withdrawn card count in " + page.name
                )
            if ("nissan-note-2021-227" in html or
                    "mercedes-a180-2020-front.webp" in html or
                    "mercedes-a180-2020-rear.webp" in html):
                raise RuntimeError("PAPAUTO_POLICY: rejected photo link survived " + page.name)
            if page.name.startswith("premium-"):
                html = html.replace("12 подтверждённых аукционных лотов",
                                    "11 опубликованных аукционных лотов")
                html = html.replace("<strong>12</strong><small>реальных примеров",
                                    "<strong>11</strong><small>реальных примеров")
                html = html.replace("ниже — 12 аукционных лотов",
                                    "ниже — 11 аукционных лотов")
                html = html.replace("Все аукционные лоты · 12",
                                    "Все аукционные лоты · 11")
                html = html.replace("🇯🇵 Япония · 12", "🇯🇵 Япония · 11")
                html = html.replace("Показано 12 аукционных автомобилей",
                                    "Показано 11 аукционных автомобилей")
            if page.name == "index.html":
                html = html.replace(
                    "Все 25 лотов с фотографиями и статистикой",
                    "Все 24 лота с фотографиями и статистикой",
                    1,
                )
            if page.name == "auction-lots.html":
                for original, screened in (
                    ("25 аукционных автомобилей", "24 аукционных автомобиля"),
                    ("25 завершённых японских аукционных лотов",
                     "24 завершённых японских аукционных лота"),
                    ("25 реальных лотов", "24 реальных лота"),
                    ("Показаны все 25 автомобилей", "Показаны все 24 автомобиля"),
                ):
                    html = html.replace(original, screened, 1)
        if page.name == "gallery.html":
            html = html.replace("Аукционная статистика 25 моделей",
                                "Аукционная статистика 24 модели", 1)
        def approved_img(match):
            tag = match.group(0)
            src = re.search(r"""src\s*=\s*["']([^"']+)["']""", tag, re.I)
            url = src.group(1) if src else ""
            # Do not allow even a direct <img> on a legacy page to resurrect
            # visually rejected street/dealer photos of Audi Q2/Q3.
            if url.lstrip("/") in QUARANTINED_OUTDOOR_MEDIA:
                return ""
            if ((re.fullmatch(r"/assets/auction/home/[a-z0-9-]+[.]jpg",url)
                  or re.fullmatch(r"/assets/premium-auctions/[a-z0-9-]+[.]webp",url)
                  or re.fullmatch(r"/assets/auction/approved/[a-z0-9-]+[.](?:jpg|jpeg|png|webp)",url))
                 and (ROOT / url.lstrip("/")).is_file()
                 or url in {"/assets/papauto-logo.svg","/assets/visual/fallback-vehicle.svg"}):
                return tag
            return ""
        html = re.sub(r"<img\b[^>]*>", approved_img, html, flags=re.I | re.S)
        html = re.sub(r"<source\b[^>]*>", "", html, flags=re.I | re.S)
        page.write_text(html, encoding="utf-8")
        if re.search(r"<img[^>]+src\s*=\s*[\"']https?://", html, flags=re.I):
            raise RuntimeError("External vehicle photograph found: " + page.name)

    public_paths = set(copied)
    tombstones = []
    for current_dir, dirs, filenames in os.walk(ROOT):
        dirs[:] = sorted(
            d for d in dirs
            if d not in WALK_EXCLUDE and not (Path(current_dir) / d).is_symlink()
        )
        for filename in sorted(filenames):
            src = Path(current_dir) / filename
            if src.is_symlink() or not src.is_file():
                continue
            relative = src.relative_to(ROOT)
            url_path = relative.as_posix()
            if url_path in public_paths or relative.parts[0] in WALK_EXCLUDE:
                continue
            unsafe = (
                src.suffix.lower() in PROTECTED_SUFFIXES
                or src.name in PROTECTED_NAMES
                or src.name.startswith(".env")
                or relative.parts[0] in PROTECTED_DIRS
            )
            if not unsafe:
                continue
            dest = TARGET / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(TOMBSTONE)
            tombstones.append(url_path)

    # Never allow the actual contents of a protected source file into the
    # static site output. Only the fixed, non-sensitive placeholder may exist.
    for path in tombstones:
        if (TARGET / path).read_bytes() != TOMBSTONE:
            raise RuntimeError("Protected asset was not safely replaced")

    # Render's CDN may continue serving deleted static file URLs. Publish fresh
    # noindex retirement pages to overwrite any previously cached third-party
    # marketplace articles. These routes are not listed in the sitemap.
    retired_legacy_pages = (
        "drom-novosibirsk-2026.html",
        "novosibirsk-avto-bez-probega-2026.html",
    )
    retirement_html = (
        '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
        '<meta name="robots" content="noindex,nofollow">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Страница удалена | PAPAUTO</title></head>'
        '<body data-page-retired="true"><main><h1>Страница удалена</h1>'
        '<p>Информация более не публикуется. Актуальный каталог и подбор автомобилей доступны на PAPAUTO.</p>'
        '<p><a href="/catalog.html">Каталог автомобилей PAPAUTO</a></p>'
        '</main></body></html>'
    )
    for retired in retired_legacy_pages:
        if retired in public_paths:
            raise RuntimeError("Retired route was reintroduced: " + retired)
        (TARGET / retired).write_text(retirement_html, encoding="utf-8")

    required = {"index.html", "catalog.html", "styles.css", "app.js",
                "robots.txt", "sitemap.xml", "assets/papauto-logo.svg",
                "data/vehicle-examples.json"}
    missing = required.difference(copied)
    if missing:
        raise RuntimeError("Public site build missing files: " + ", ".join(sorted(missing)))

    print(f"Prepared {len(copied)} public files and {len(tombstones)} safe tombstones in {TARGET.name}/")
    return copied


if __name__ == "__main__":
    copy_public_files()
