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
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "render-public"
ROOT_SUFFIXES = {".html", ".css", ".js", ".xml", ".webmanifest"}
# Only explicitly allowed domain-verification text files may be published; others remain tombstoned.
# Catalog publishing is locked to the owner-reviewed photo+sheet baseline by verify_publication_approval.py.
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


# Only UI CSS declarations get recolored; never alter real auction images,
# embedded data, auction records, listing IDs or hyperlinks.
def _warm_color_code(value: str) -> str:
    import colorsys
    h = value.lstrip("#")
    if len(h) not in (3, 4, 6, 8):
        return value
    if len(h) <= 4:
        h = "".join(char * 2 for char in h)
    red, green, blue = (int(h[pos:pos+2], 16) for pos in (0, 2, 4))
    if not (blue > red + 5 and blue >= green - 12):
        return value
    light = (max(red, green, blue) + min(red, green, blue)) / 510
    sat = .30 if light < .14 else (.34 if light < .45 else (.25 if light < .7 else .28))
    light = min(.975, .23 if light < .14 else (.27 if light < .24 else light))
    red, green, blue = colorsys.hls_to_rgb(28 / 360, light, sat)
    rgb = "".join(f"{round(channel*255):02x}" for channel in (red, green, blue))
    return "#" + rgb + (h[6:] if len(h) == 8 else "")


def _warm_inline_css(html: str) -> str:
    # Correct legacy blue literals only in UI styles, not auction content.
    pattern = re.compile(r"#[a-fA-F0-9]{3,8}\b")
    def recolor(css: str) -> str:
        return pattern.sub(lambda match: _warm_color_code(match.group(0)), css)
    html = re.sub(
        r"<style\b[^>]*>[\s\S]*?</style>",
        lambda match: recolor(match.group(0)), html, flags=re.I,
    )
    html = re.sub(
        r"""\bstyle=(['"])(.*?)\1""",
        lambda match: "style=" + match.group(1) + recolor(match.group(2)) + match.group(1),
        html, flags=re.I | re.S,
    )
    html = re.sub(
        r"""<meta\b[^>]*\bname=['"]theme-color['"][^>]*>""",
        lambda match: re.sub(r"""\bcontent=['"][^'"]+['"]""",
                             'content="#f8f1e8"', match.group(0), count=1, flags=re.I),
        html, flags=re.I,
    )
    return html


def copy_public_files() -> list[str]:
    from verify_publication_approval import verify_frozen_inputs, verify_published_output
    # Block unapproved new/edited lot data, photos and sheets BEFORE any build output.
    verify_frozen_inputs()
    from verify_china_order_release import verify as verify_china_order
    china_order_photos = verify_china_order(ROOT)
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
        if src.is_file() and not src.is_symlink() and (src.suffix.lower() in ROOT_SUFFIXES or src.name in PUBLIC_TEXT_FILES or src.name == "favicon.svg"):
            dst = TARGET / src.name
            shutil.copy2(src, dst)
            copied.append(dst.relative_to(TARGET).as_posix())

    # Publish only owner-curated model landing pages; never copy arbitrary repository folders.
    model_root = ROOT / "models"
    if model_root.is_dir() and not model_root.is_symlink():
        for src in sorted(model_root.glob("*.html")):
            if src.is_file() and not src.is_symlink():
                dst = TARGET / "models" / src.name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                copied.append(dst.relative_to(TARGET).as_posix())

    # Fail the deploy rather than silently publish sitemap URLs that return 404.
    if model_root.is_dir():
        expected_model_pages = list(model_root.glob("*.html"))
        if len(expected_model_pages) != 135 or any(not (TARGET / "models" / page.name).is_file() for page in expected_model_pages):
            raise RuntimeError("PAPAUTO_SEO: expected 135 published model pages")

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
            if folder == 'assets' and (relative.parts[:2] == ('assets','demo') or (relative.parts[:2] == ('assets','visual') and relative.as_posix() not in {'assets/visual/fallback-vehicle.svg', 'assets/visual/papauto-thursday-approved-editorial-artwork-20261112.webp', 'assets/visual/papauto-approved-bmw-hero-20261115.webp'})):
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
    # Customer policy: NEVER publish text-only vehicle cards as auction lots.
    # Every visible premium listing must carry the matched photo, mileage and sheet.
    for page_name in ("premium-japan-korea.html", "premium-mobile-photo-demo.html"):
        html = (ROOT / page_name).read_text(encoding="utf-8")
        if any(token in html for token in (
            'data-selection-grid', 'premium-expanded-catalog.js',
            'id="market-catalog"', 'selection-model-entry',
        )):
            raise RuntimeError("PAPAUTO_POLICY: text-only vehicle cards in " + page_name)
        cards = re.findall(r'<article class="real-card"[^>]*>[\s\S]*?</article>', html)
        if len(cards) != 12:
            raise RuntimeError("PAPAUTO_POLICY: missing approved premium auction cards in " + page_name)
        for card in cards:
            if not all(token in card for token in (
                'real-img-main', 'real-img-sheet', '<span>Пробег</span>', 'real-trim',
            )):
                raise RuntimeError("PAPAUTO_POLICY: auction photo/mileage/sheet missing in " + page_name)
            if '/assets/demo/' in card or '/assets/visual/' in card:
                raise RuntimeError("PAPAUTO_POLICY: street image in auction card")
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

    # Include the fixed owner-selected set alongside the licensed import registry.
    from compile_auction_gallery import OWNER_SELECTION, compile_published_gallery
    gallery_result = compile_published_gallery(TARGET, owner_path=OWNER_SELECTION)
    # User explicitly approved the 100-card PDF on 2026-11-15: 97 newly
    # selected auction lots and 3 already in our existing 35-lot public set.
    # Fail closed if any unexpected/unreviewed extra lot sneaks into release.
    if gallery_result["count"] != 659 or gallery_result["new"] != 624:
        raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: wrong 100-card owner-reviewed release")
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
            if page.name == "china-order.html" and url.lstrip("/") in china_order_photos:
                return tag
            # Do not allow even a direct <img> on a legacy page to resurrect
            # visually rejected street/dealer photos of Audi Q2/Q3.
            if url.lstrip("/") in QUARANTINED_OUTDOOR_MEDIA:
                return ""
            if ((re.fullmatch(r"/assets/auction/home/[a-z0-9-]+[.]jpg",url)
                  or re.fullmatch(r"/assets/premium-auctions/[a-z0-9-]+[.]webp",url)
                  or re.fullmatch(r"/assets/auction/approved/[a-z0-9-]+[.](?:jpg|jpeg|png|webp)",url))
                 and (ROOT / url.lstrip("/")).is_file()
                 or url in {"/assets/papauto-logo.svg", "/assets/papauto-red-brand.svg",
                            "/assets/visual/fallback-vehicle.svg",
                            "/assets/visual/papauto-thursday-approved-editorial-artwork-20261112.webp",
                            "/assets/visual/papauto-approved-bmw-hero-20261115.webp"}):
                return tag
            return ""
        html = re.sub(r"<img\b[^>]*>", approved_img, html, flags=re.I | re.S)
        html = re.sub(r"<source\b[^>]*>", "", html, flags=re.I | re.S)
        # Keep the specifically approved Thursday marketing illustration in HTML,
        # not only in copied files. Reject a broken deployment if it disappears.
        if page.name == "index.html":
            hero_asset = "assets/visual/papauto-approved-bmw-hero-20261115.webp"
            if (not (TARGET / hero_asset).is_file()
                    or f'<img src="/{hero_asset}"' not in html):
                raise RuntimeError("PAPAUTO_HERO: approved BMW artwork stripped from public homepage")
        # Every customer-facing page receives the same final warm stylesheet.
        # Leave search engine verification HTML (no head/body) untouched.
        if "</head>" in html.lower() and re.search(r"<body\b", html, flags=re.I):
            html = _warm_inline_css(html)
            warm_stylesheet = "papauto-warm-interior.css"
            if not (TARGET / warm_stylesheet).is_file():
                raise RuntimeError("PAPAUTO_WARM: site theme CSS missing")
            html = re.sub(
                r"</head>",
                '<link rel="stylesheet" href="/papauto-warm-interior.css?v=20261115-all-site-v4"></head>',
                html, count=1, flags=re.I,
            )
            if page.name != "index.html":
                def add_skin(match):
                    tag = match.group(0)
                    if 'class="' in tag:
                        return tag.replace('class="', 'class="papauto-warm-interior ', 1)
                    if "class='" in tag:
                        return tag.replace("class='", "class='papauto-warm-interior ", 1)
                    return tag[:-1] + ' class="papauto-warm-interior">'
                html, count = re.subn("<body([^>]*)>", add_skin, html, count=1, flags=re.I)
                if count != 1:
                    raise RuntimeError("PAPAUTO_WARM: body not tagged " + page.name)
            if html.count("papauto-warm-interior.css") != 1:
                raise RuntimeError("PAPAUTO_WARM: stylesheet missing/duplicated " + page.name)
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
        '<title>Страница удалена | PAPAUTO</title>'
        '<link rel="stylesheet" href="/papauto-warm-interior.css?v=20261115-all-site-v4">'
        '</head>'
        '<body class="papauto-warm-interior" data-page-retired="true">'
        '<main><h1>Страница удалена</h1>'
        '<p>Информация более не публикуется. Актуальный каталог и подбор автомобилей доступны на PAPAUTO.</p>'
        '<p><a href="/catalog.html">Каталог автомобилей PAPAUTO</a></p>'
        '</main></body></html>'
    )
    for retired in retired_legacy_pages:
        if retired in public_paths:
            raise RuntimeError("Retired route was reintroduced: " + retired)
        (TARGET / retired).write_text(retirement_html, encoding="utf-8")

    # Publish search entry points requested by the owner for the published catalogue on 2026-11-16.
    # The detail-page SEO metadata generated here is length-checked by the lot release test.
    from publish_lot_search import publish
    published_lot_count = publish(TARGET)
    lot_sitemap = TARGET / "sitemap-lots.xml"
    if published_lot_count != 659 or not lot_sitemap.is_file():
        raise RuntimeError("PAPAUTO_SEO: the approved lot sitemap is missing or incomplete")
    import xml.etree.ElementTree as ET
    lot_sitemap_tree = ET.parse(lot_sitemap)
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    lot_urls = [node.text for node in lot_sitemap_tree.findall(f"{ns}url/{ns}loc")]
    if len(lot_urls) != published_lot_count or len(set(lot_urls)) != published_lot_count:
        raise RuntimeError("PAPAUTO_SEO: dedicated lot sitemap does not match approved pages")
    # The released lot pages were updated on 2026-11-22. Their sitemap
    # entries must include valid lastmod dates so crawlers can detect changes.
    lot_nodes = lot_sitemap_tree.findall(f"{ns}url")
    lot_dates = [node.findtext(f"{ns}lastmod") for node in lot_nodes]
    if len(lot_dates) != published_lot_count or any(
            not date or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", date)
            for date in lot_dates):
        raise RuntimeError("PAPAUTO_SEO: lot sitemap lastmod missing or invalid")
    # Expose only the approved first vehicle photograph of each published lot.
    # Google accepts image sitemap extensions, and no unrelated stock photos
    # should enter the public catalogue or the image sitemap.
    image_ns = "{http://www.google.com/schemas/sitemap-image/1.1}"
    image_urls = [node.findtext(f"{image_ns}image/{image_ns}loc")
                  for node in lot_nodes]
    if (len(image_urls) != published_lot_count or
            any(not url or not url.startswith("https://papauto.ru/assets/")
                or not (TARGET / url.removeprefix("https://papauto.ru/")).is_file()
                for url in image_urls)):
        raise RuntimeError("PAPAUTO_SEO: image sitemap missing exact auction photos")
    core_tree = ET.parse(TARGET / "sitemap.xml")
    core_url_list = [node.text for node in core_tree.findall(f"{ns}url/{ns}loc")]
    core_urls = set(core_url_list)
    if len(core_url_list) != len(core_urls):
        raise RuntimeError("PAPAUTO_SEO: duplicate URLs in main sitemap")
    from urllib.parse import urlsplit, unquote
    for url in core_url_list:
        if not url:
            raise RuntimeError("PAPAUTO_SEO: empty URL in main sitemap")
        parts = urlsplit(url)
        if (parts.scheme != "https" or parts.netloc != "papauto.ru"
                or parts.query or parts.fragment or not parts.path.startswith("/")):
            raise RuntimeError("PAPAUTO_SEO: noncanonical sitemap URL: " + url)
        relative = unquote(parts.path).lstrip("/")
        if ".." in relative.split("/"):
            raise RuntimeError("PAPAUTO_SEO: invalid sitemap path: " + url)
        target_page = TARGET / relative
        if parts.path.endswith("/"):
            target_page = target_page / "index.html"
        if not target_page.is_file():
            raise RuntimeError("PAPAUTO_SEO: sitemap points to missing page: " + url)
    # Every released model landing page must be discoverable through the main sitemap.
    published_models = {"https://papauto.ru/models/" + page.name
                        for page in (TARGET / "models").glob("*.html")}
    sitemap_models = {url for url in core_urls if url.startswith("https://papauto.ru/models/")}
    if len(published_models) != 135 or published_models != sitemap_models:
        raise RuntimeError("PAPAUTO_SEO: model pages and sitemap disagree: "
                           + str(sorted(published_models ^ sitemap_models)))
    if set(lot_urls) & core_urls or "https://papauto.ru/auction-lot-index.html" not in core_urls:
        raise RuntimeError("PAPAUTO_SEO: duplicate lot URLs or missing auction index in main sitemap")

    # Keep public archive count synchronized with the approved registry. A previous
    # page generator could show 639 even when the release contained 641 lots.
    index_page = (TARGET / "auction-lot-index.html").read_text(encoding="utf-8")
    if f"Количество опубликованных аукционных примеров: {published_lot_count}." not in index_page:
        raise RuntimeError("PAPAUTO_SEO: stale auction index count")
    for page_name in ("catalog.html", "auction-lots.html", "gallery.html"):
        content = (TARGET / page_name).read_text(encoding="utf-8")
        if f"Все аукционные карточки ({published_lot_count})" not in content:
            raise RuntimeError("PAPAUTO_SEO: stale archive navigation count: " + page_name)

    # Attach only already screened public auction examples to all model pages.
    from link_model_statistics import render as link_model_statistics
    model_coverage = link_model_statistics(TARGET, published_registry, china_order_photos)
    if model_coverage['supplier_cards'] != model_coverage['supplier_matches']:
        raise RuntimeError('PAPAUTO_MODEL_STATS: missing inline supplier cards')

    # The gallery compiler generates /lots/*.html after the initial page loop.
    # Reconcile every finished HTML page with the global warm skin, including
    # exact auction lot pages and legacy retirement pages. Photo bytes are untouched.
    for rendered in sorted(TARGET.rglob("*.html")):
        contents = rendered.read_text(encoding="utf-8")
        if "</head>" not in contents.lower() or not re.search(r"<body\b", contents, flags=re.I):
            continue
        contents = _warm_inline_css(contents)
        if "papauto-warm-interior.css" not in contents:
            contents = re.sub(
                r"</head>",
                '<link rel="stylesheet" href="/papauto-warm-interior.css?v=20261115-all-site-v4"></head>',
                contents, count=1, flags=re.I,
            )
        if rendered.name != "index.html":
            body_match = re.search(r"<body\b[^>]*>", contents, flags=re.I)
            if not body_match:
                raise RuntimeError("PAPAUTO_WARM: generated body missing: " + str(rendered))
            if "papauto-warm-interior" not in body_match.group(0):
                def add_skin(match):
                    tag = match.group(0)
                    if 'class="' in tag:
                        return tag.replace('class="', 'class="papauto-warm-interior ', 1)
                    if "class='" in tag:
                        return tag.replace("class='", "class='papauto-warm-interior ", 1)
                    return tag[:-1] + ' class="papauto-warm-interior">'
                contents = re.sub(r"<body\b[^>]*>", add_skin, contents, count=1, flags=re.I)
        if contents.count("papauto-warm-interior.css") != 1:
            raise RuntimeError("PAPAUTO_WARM: missing/duplicate stylesheet " + str(rendered))
        # Link only cards already published by the photo/rights gate to the calculator.
        def estimate_link(key, market):
            return ('<a class="pa-estimate-card-link" href="/?view=calculator&amp;market='
                    + quote(market, safe="") + '&amp;vehicle=' + quote(key, safe="")
                    + '" style="display:inline-block;margin:8px 0;color:inherit;font-weight:500;text-decoration:underline">Рассчитать стоимость →</a>')
        if rendered.name in {"index.html", "auction-lots.html", "gallery.html"}:
            def add_lot_estimate(match):
                article = match.group(0)
                hit = re.search(r'\bdata-(?:lot-id|lot)="([a-z0-9-]+)"', article)
                if not hit or hit.group(1) not in public_ids:
                    return article
                return article.replace("</article>", estimate_link("lot:" + hit.group(1), "japan") + "</article>", 1)
            contents = re.sub(r'<article\b[^>]*>[\s\S]*?</article>', add_lot_estimate, contents)
            if rendered.name == "gallery.html":
                contents = contents.replace("/gallery.js?v=20261124-perf", "/gallery.js?v=20261124-estimate")
        elif rendered.name == "china-order.html":
            def add_china_estimate(match):
                article = match.group(0)
                hit = re.search(r'<img\b[^>]*\bsrc="(/assets/china-order/[^"]+)"', article)
                if not hit or hit.group(1).lstrip("/") not in china_order_photos:
                    return article
                return article.replace("</article>", estimate_link("cn:" + hit.group(1), "china") + "</article>", 1)
            contents = re.sub(r'<article class="cn-example"[^>]*>[\s\S]*?</article>', add_china_estimate, contents)
        elif rendered.parent == TARGET / "lots" and rendered.stem in public_ids:
            public_market = next(lot["market"] for lot in published_registry["lots"] if lot["id"] == rendered.stem)
            contents = re.sub(r"</main>", estimate_link("lot:" + rendered.stem, public_market) + "</main>", contents, count=1, flags=re.I)
        rendered.write_text(contents, encoding="utf-8")

    required = {"index.html", "catalog.html", "styles.css", "app.js",
                "robots.txt", "sitemap.xml", "assets/papauto-logo.svg",
                "data/vehicle-examples.json"}
    missing = required.difference(copied)
    if missing:
        raise RuntimeError("Public site build missing files: " + ", ".join(sorted(missing)))

    # Final gate inspects the full published HTML/data/image bytes, not a preview.
    # Re-check inline supplier images after final theme and calculator passes.
    supplier_card_count = 0
    for model_page in (TARGET / "models").glob("*.html"):
        model_html = model_page.read_text(encoding="utf-8")
        cards = re.findall(r'<article class="pa-model-lot pa-model-supplier"[^>]*>[\s\S]*?</article>', model_html)
        for card in cards:
            photos = re.findall(r'<img\b[^>]*\bsrc="(/assets/china-order/[^"]+)"', card)
            if (not model_page.stem.startswith("china-") or len(photos) != 1
                    or photos[0].lstrip("/") not in china_order_photos
                    or not all(x in card for x in ("Двигатель", "Пробег", "Рассчитать стоимость", "Подобрать аналог"))
                    or re.search(r'href="https?://', card)):
                raise RuntimeError("PAPAUTO_MODEL_STATS: invalid supplier card " + model_page.stem)
        supplier_card_count += len(cards)
    if supplier_card_count != model_coverage["supplier_cards"]:
        raise RuntimeError("PAPAUTO_MODEL_STATS: inline cards lost after build")
    print(f"PAPAUTO_MODEL_SUPPLIER_CARDS_OK: {supplier_card_count}")

    verify_published_output(TARGET)

    print(f"Prepared {len(copied)} public files and {len(tombstones)} safe tombstones in {TARGET.name}/")
    return copied


if __name__ == "__main__":
    copy_public_files()
