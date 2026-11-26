"""Canonical navigation for the 15 verified legacy model redirects.
Keep archived source pages intact; normalize generated customer-facing links.
"""
import re
from urllib.parse import urlsplit, urljoin, urlunsplit

BASE = "https://papauto.ru"
MODEL_REDIRECTS = {
    "/honda-fit-japan.html": "/models/japan-honda-fit.html",
    "/honda-freed-japan.html": "/models/japan-honda-freed.html",
    "/honda-vezel-japan.html": "/models/japan-honda-vezel.html",
    "/nissan-note-japan.html": "/models/japan-nissan-note.html",
    "/suzuki-jimny-japan.html": "/models/japan-suzuki-jimny.html",
    "/toyota-aqua-japan.html": "/models/japan-toyota-aqua.html",
    "/toyota-corolla-japan.html": "/models/japan-toyota-corolla.html",
    "/toyota-prius-japan.html": "/models/japan-toyota-prius.html",
    "/toyota-sienta-japan.html": "/models/japan-toyota-sienta.html",
    "/toyota-vitz-japan.html": "/models/japan-toyota-vitz.html",
    "/hyundai-avante-korea.html": "/models/korea-hyundai-avante-elantra.html",
    "/kia-k5-korea.html": "/models/korea-kia-k5.html",
    "/byd-song-plus-china.html": "/models/china-byd-song-plus.html",
    "/geely-monjaro-china.html": "/models/china-geely-monjaro.html",
    "/haval-jolion-china.html": "/models/china-haval-jolion.html",
}

HREF = re.compile(r"""(\bhref\s*=\s*)(["'])([^"']*)\2""", re.I)

def canonical_href(value, page_path):
    # Every legacy calculator navigation entry opens the single current calculator.
    if value == "#import-estimate" and page_path in ("/premium-japan-korea.html", "/premium-mobile-photo-demo.html"):
        return "/?view=calculator"
    if not value or value.startswith(("#", "?")):
        return value
    resolved = urlsplit(urljoin(BASE + page_path, value))
    if resolved.scheme not in ("http", "https") or resolved.netloc not in ("papauto.ru", "www.papauto.ru"):
        return value
    if resolved.path == "/premium-japan-korea.html" and resolved.fragment == "import-estimate":
        return "/?view=calculator"
    destination = MODEL_REDIRECTS.get(resolved.path)
    if not destination:
        return value
    # An absolute URL must remain absolute (canonical and structured metadata).
    original = urlsplit(value)
    absolute = bool(original.scheme or original.netloc)
    return urlunsplit(("https" if absolute else "", "papauto.ru" if absolute else "",
                       destination, resolved.query, resolved.fragment))

def rewrite_html(html, page_path):
    return HREF.sub(lambda m: m.group(1) + m.group(2) +
                    canonical_href(m.group(3), page_path) + m.group(2), html)

def rewrite_public(target):
    for old, new in MODEL_REDIRECTS.items():
        if not (target / new.lstrip("/")).is_file():
            raise RuntimeError("Missing canonical model target: " + new)
    changed = 0
    for page in sorted(target.rglob("*.html")):
        path = "/" + page.relative_to(target).as_posix()
        source = page.read_text(encoding="utf-8")
        updated = rewrite_html(source, path)
        if updated != source:
            page.write_text(updated, encoding="utf-8")
            changed += 1
    print("PAPAUTO_CANONICAL_NAVIGATION_OK:", changed, "HTML pages updated")
    return changed
