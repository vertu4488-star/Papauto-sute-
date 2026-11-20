"""Narrow owner approval, 2026-11-20: supplier examples, NOT auction lots or third-party license."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDS = "001,002,003,004,005,006,007,008,009,010,011,013,014,015,016,017,018,019,020,021,022,023,024,026,027,028,029,030,033,034,035,037,038,039,040,041,042,045,046,049,050,051,052,053,054,055,059,064,068".split(",")
DIGEST = "c8a31991d39edb5921295bc4f759b9d97d04136feefa597999b0625868490c95"
PREFIX = "assets/china-order/owner-20261120/"
PAGE = "china-order.html"

def verify(root=ROOT):
    root = Path(root)
    media = root / PREFIX
    expected = {PREFIX + ident + ".jpg" for ident in IDS}
    found = {p.relative_to(root).as_posix() for p in (root / "assets/china-order").rglob("*") if p.is_file() or p.is_symlink()}
    if found != expected:
        raise RuntimeError("CHINA_ORDER: unexpected or missing image")
    hashes = []
    for ident in IDS:
        p = media / (ident + ".jpg")
        b = p.read_bytes()
        if p.is_symlink() or not b.startswith(b"\xff\xd8\xff") or len(b)<500:
            raise RuntimeError("CHINA_ORDER: invalid photo " + ident)
        hashes.append([ident,hashlib.sha256(b).hexdigest()])
    if hashlib.sha256(json.dumps(hashes,separators=(",",":")).encode()).hexdigest()!=DIGEST:
        raise RuntimeError("CHINA_ORDER: photo changed from owner preview")
    html = (root/PAGE).read_text(encoding="utf-8")
    if re.findall(r'<img\b[^>]*\bsrc="([^"]+)"',html) != ["/"+PREFIX+i+".jpg" for i in IDS]:
        raise RuntimeError("CHINA_ORDER: photo identity mismatch")
    for p in root.glob("*.html"):
        if p.name != PAGE and "/assets/china-order/" in p.read_text(encoding="utf-8"):
            raise RuntimeError("CHINA_ORDER: supplier photo outside dedicated section")
    return expected
