"""Build a strict, public-only directory for the PAPAUTO Render static site.

Only whitelisted public assets are copied. Never publish the repository root:
it also contains Python API code, tests, GitHub workflows and build scripts.
Run from the repository checkout with Python 3.11+.
"""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "render-public"
ROOT_SUFFIXES = {".html", ".css", ".js", ".xml", ".txt", ".webmanifest"}
PUBLIC_FOLDERS = {
    "assets": {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico"},
    "data": {".json"},
}


def copy_public_files() -> list[str]:
    # This is a generated output directory; never accept a symbolic-link target.
    if TARGET.is_symlink():
        raise RuntimeError("Refusing to overwrite a symlinked publish directory")
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(mode=0o755)
    copied = []

    for src in sorted(ROOT.iterdir()):
        if src.is_file() and not src.is_symlink() and src.suffix.lower() in ROOT_SUFFIXES:
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

    required = {"index.html", "catalog.html", "styles.css", "app.js",
                "robots.txt", "sitemap.xml", "assets/papauto-logo.svg",
                "data/vehicle-examples.json"}
    missing = required.difference(copied)
    if missing:
        raise RuntimeError("Public site build missing files: " + ", ".join(sorted(missing)))

    forbidden = [file for file in TARGET.rglob("*") if file.is_file()
                 and file.suffix.lower() in {".py", ".md", ".yml", ".yaml", ".toml"}]
    if forbidden:
        raise RuntimeError("Unsafe source files in static publish output")
    print(f"Prepared {len(copied)} static files in {TARGET.name}/")
    return copied


if __name__ == "__main__":
    copy_public_files()
