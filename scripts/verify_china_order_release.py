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
EXTRA_PREFIX = "assets/china-order/owner-20261120-batch30/"
EXTRA_HASHES = {
    "049": "9cc8b3627a88dbe6ab24a9259239872417d1d12e16bd46927833b52c2dee41ef",
    "013": "f99491a6292f3bf6987cd5f0593fced3a28aeb94e97c5997b7239fc60a11068c",
    "030": "32fa7713de1ec142183fe1b5f2547f33bc335ec543d5216214213d3d9cb35375",
    "051": "f8f252aba4939e4a4c0872bc99904f3d4d46e96ed3a9b89dffa7dec46a2cb79e",
    "064": "8d4fa2271eca4fa59d97a219e770dbf9ac625acc1501a02beef47e95d796d1d1",
    "052": "4f521fce4a2af1e913310962849955eadc470be4d7908c9a067183ab7632443b",
    "011": "16c7e2322a89779dadaeb68b9266e8dd3775978ed5d5fdce8f81c10ca1864eb1",
    "081": "39a974f57441eaf3b47f975d2bb0ac8013cc412c2177a8966005e207e646487f",
    "083": "89e3a8f6e1e42b26358c4ca2c700a3a879bcc8b6d13186c10641c3fe17dca0d1",
    "088": "e661dfa9c20c59692140c522dc6d50727fa954446a8de20de8fe7c97d7c2f6bb",
    "082": "5e557b9c77466545596e8f19b9b93709f699b6f0364e2816a918c86749d6e7bb",
    "037": "63324f32ea7777bb3724f44944b635e4767584835371a1af53cb59ceade8d8d0",
    "054": "65846e2cc3da448e3b6deebd8b9fec29b423ff08164efff172053c304254e764",
    "077": "d71897ecd32cfc7a8e4dcc8c65a492efefe29ec277f1f908b5fcf1f44b577362",
    "078": "73f7fa63034bdea21771b775a5a7f4a54554dba4cac9699d93bd4647582f08da",
    "080": "0c8acdb314a5521163148eb32a2c6265eb1e1cde5cdb8ee4e1870aafadd4feac",
    "044": "1f628e517f38e6c4471be6a3a512a90cb8d10ba201868cfbfb89794d3ed62db5",
    "045": "9a378a63b91441fdba14cab09ffdfd58aa2d79871c759af40758c35ca33c46ef",
    "055": "12bbbfcae224ac0231335a40bf2111c75c22d27567034a864e8fad23f01ef3ad",
    "069": "4e35cd9f25c138761f83914fb3e6286a4ce700361b404782f3cf8ce947f5dcbf",
    "007": "4143243792d184ffa335527af42d8a52eab5b5d6495f2ceba716cac7332bbf69",
    "012": "849a3ef6159d788083945442e2090c68f30a26e602857911ed9bbb4d7f4d57ce",
    "018": "cd67edf5728dd0030d09cf3839ed086e5f3458fe26fbde33f8b8cc0d1a06914f",
    "021": "5479520b49358a815c5c98f988b794b28dd4f10ba3c281f7a168e9c6242ab5e3",
    "022": "76c723114bb5881806bdc3404de94fd140ad0c4e855cdc73ba9e81b391b8143d",
    "025": "24a8d116c3abcf313b2a20488f99fa7049a4934555dbc2ae493acd0539ef6878",
    "027": "dbf19b7a67e1ad0e7d342652754bd77915b4362e941bc9005b183606272c3793",
    "028": "638dd31d2c02a4c992258b1a7793d0ab4d2a91947facaa19e394fd9d06bce3b6",
    "032": "c1bac8dc045981cb3d8a217a136698c90cbd7bbb5a82ebf0973c478559aa63b6",
    "035": "07546e4455314988c88bec1c96ea23f41c57dee61b1d67cfecef975ec33287d4"
}


def verify(root=ROOT):
    root = Path(root)
    media = root / PREFIX
    expected = {PREFIX + ident + ".jpg" for ident in IDS} | {EXTRA_PREFIX + ident + ".jpg" for ident in EXTRA_HASHES}
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
    for ident, digest in EXTRA_HASHES.items():
        p = root / EXTRA_PREFIX / (ident + ".jpg")
        b = p.read_bytes()
        if p.is_symlink() or len(b)<500 or not b.startswith(b"\xff\xd8\xff") or hashlib.sha256(b).hexdigest()!=digest:
            raise RuntimeError("CHINA_ORDER: second batch photo mismatch " + ident)
    html = (root/PAGE).read_text(encoding="utf-8")
    if re.findall(r'<img\b[^>]*\bsrc="([^"]+)"',html) != ["/"+PREFIX+i+".jpg" for i in IDS] + ["/"+EXTRA_PREFIX+i+".jpg" for i in EXTRA_HASHES]:
        raise RuntimeError("CHINA_ORDER: photo identity mismatch")
    for p in root.glob("*.html"):
        if p.name != PAGE and "/assets/china-order/" in p.read_text(encoding="utf-8"):
            raise RuntimeError("CHINA_ORDER: supplier photo outside dedicated section")
    return expected
