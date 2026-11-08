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

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "render-public"
ROOT_SUFFIXES = {".html", ".css", ".js", ".xml", ".webmanifest"}
PUBLIC_TEXT_FILES = {"robots.txt", "ads.txt", "security.txt"}
# Some former Render builds published the whole repository. Explicit tombstones
# replace old assets that otherwise remain fetchable at their old URLs.
TOMBSTONE = b"404 Not Found - PAPAUTO\n"
PROTECTED_SUFFIXES = {".py", ".pyc", ".md", ".toml", ".yaml", ".yml", ".ini", ".cfg", ".sh", ".sql", ".log", ".lock", ".txt"}
PROTECTED_NAMES = {".gitignore", ".python-version", "Dockerfile", "Makefile", "LICENSE", "render.yaml"}
PROTECTED_DIRS = {".github", "scripts", "tests", "research", "content", "docs"}
WALK_EXCLUDE = {".git", "render-public", "node_modules", "__pycache__", ".pytest_cache", ".venv", "venv", ".mypy_cache", ".ruff_cache"}
PUBLIC_FOLDERS = {
    "assets": {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico"},
    "data": {".json"},
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
            dst = TARGET / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(dst.relative_to(TARGET).as_posix())

    # Only our own explicitly approved auction photos may be published.
    # This also retires historical hotlinked photos on existing SEO/model pages.
    for page in TARGET.glob("*.html"):
        html = page.read_text(encoding="utf-8")
        def approved_img(match):
            tag = match.group(0)
            src = re.search(r"""src\s*=\s*["']([^"']+)["']""", tag, re.I)
            url = src.group(1) if src else ""
            if url.startswith("/assets/auction/") or url == "/assets/papauto-logo.svg":
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
