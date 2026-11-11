#!/usr/bin/env python3
"""Build a public noindex GitHub Pages preview from the strict Render static build.

URL: https://vertu4488-star.github.io/Papauto-sute-/papauto-preview/
The production domain, API, and Render deployment are not modified.
"""
from pathlib import Path
import re
import shutil

SOURCE = Path('render-public')
TARGET = Path('_github_pages_probe/papauto-preview')
PREFIX = '/Papauto-sute-/papauto-preview'
PUBLISH_EXTENSIONS = {'.html', '.css', '.js', '.json', '.svg', '.png', '.jpg', '.jpeg', '.webp', '.gif', '.ico', '.webmanifest'}
PUBLISH_FILES = {'robots.txt', 'favicon.ico', '.nojekyll'}


def replace_static_urls(value: str) -> str:
    value = re.sub(
        r'''(\b(?:href|src|action|poster|data-src)\s*=\s*)(["'])/(?!/)''',
        lambda m: m.group(1) + m.group(2) + PREFIX + '/',
        value, flags=re.I,
    )
    value = re.sub(
        r'''(["'\x60])/(?=(?:assets/|data/|[a-z0-9_.-]+\.(?:html|css|js|json|svg|xml|webmanifest)\b))''',
        lambda m: m.group(1) + PREFIX + '/',
        value, flags=re.I,
    )
    value = re.sub(
        r'''(url\(\s*["']?)/(?!/|Papauto-sute-/)''',
        lambda m: m.group(1) + PREFIX + '/',
        value, flags=re.I,
    )
    return value


def make_preview() -> None:
    if not (SOURCE / 'index.html').exists():
        raise RuntimeError('Safe static source not built; run build_static_public.py first')
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True, exist_ok=True)
    count = 0

    for source in sorted(SOURCE.rglob('*')):
        if not source.is_file() or source.is_symlink():
            continue
        if source.suffix.lower() not in PUBLISH_EXTENSIONS and source.name not in PUBLISH_FILES:
            continue
        rel = source.relative_to(SOURCE)
        if any(part.startswith('.') for part in rel.parts[:-1]):
            continue
        dest = TARGET / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix.lower() in {'.html', '.css', '.js', '.json', '.webmanifest'}:
            content = source.read_text(encoding='utf-8')
            if source.suffix.lower() == '.html':
                content = re.sub(
                    r'''<meta\b[^>]*\bname\s*=\s*["']robots["'][^>]*>''',
                    '', content, flags=re.I,
                )
                content = re.sub(
                    r'''(<head\b[^>]*>)''',
                    r'\1<meta name="robots" content="noindex,nofollow,noarchive">',
                    content, count=1, flags=re.I,
                )
                # Avoid counting GitHub Pages test visits in production analytics.
                content = re.sub(
                    r'''<script\b[^>]*\bsrc=["']https?://www\.googletagmanager\.com/[^"']+["'][^>]*>\s*</script>''',
                    '', content, flags=re.I,
                )
                content = re.sub(
                    r'''<script\b[^>]*>[^<]*window\.dataLayer[^<]*</script>''',
                    '', content, flags=re.I | re.S,
                )
                content = re.sub(
                    r'''<script\b[^>]*\bsrc=["']/metrika\.js["'][^>]*>\s*</script>''',
                    '', content, flags=re.I,
                )
            content = replace_static_urls(content)
            dest.write_text(content, encoding='utf-8')
        else:
            shutil.copy2(source, dest)
        count += 1

    (TARGET / '.nojekyll').write_text('', encoding='utf-8')
    (TARGET / 'robots.txt').write_text('User-agent: *\nDisallow: /\n', encoding='utf-8')

    # Route ONLY this isolated noindex GitHub Pages preview to the tested
    # Netlify bridge. The production site-config.js stays unchanged on Render.
    preview_config = TARGET / 'site-config.js'
    if not preview_config.is_file():
        raise RuntimeError('Public preview is missing site-config.js')
    config_text = preview_config.read_text(encoding='utf-8')
    original_api = 'https://api.papauto.ru'
    preview_api = 'https://classy-genie-e78657.netlify.app'
    if config_text.count(original_api) != 1:
        raise RuntimeError('Unexpected API config; refusing unsafe preview override')
    preview_config.write_text(
        config_text.replace(original_api, preview_api), encoding='utf-8'
    )

    index = TARGET / 'index.html'
    page = index.read_text(encoding='utf-8')
    marker = (
        '<div role="status" style="position:relative;z-index:9999;'
        'background:#fff3cd;color:#382800;padding:12px 20px;'
        'text-align:center;font:600 15px/1.4 Arial,sans-serif">'
        'ТЕСТОВАЯ КОПИЯ PAPAUTO · GitHub Pages · без VPN</div>'
    )
    if not re.search(r'<body\b[^>]*>', page, re.I):
        raise RuntimeError('Preview homepage has no body tag')
    page = re.sub(r'(<body\b[^>]*>)', lambda m: m.group(1) + marker, page, count=1, flags=re.I)
    index.write_text(page, encoding='utf-8')
    if 'name="robots" content="noindex,nofollow,noarchive"' not in page:
        raise RuntimeError('Preview noindex was not installed')
    if 'href="/catalog.html"' in page or 'src="/assets/' in page:
        raise RuntimeError('A root-relative preview URL was not rewritten')
    print(f'Built {count} public preview files at {TARGET} under {PREFIX}/')


if __name__ == '__main__':
    make_preview()
