"""PapAuto release contract: fail closed on unreviewed lots and off-site card links.

The immutable baseline corresponds to the last owner-reviewed auction set.
To change it, first present COMPLETE photo + exact auction sheet + description +
mileage to the owner, receive explicit approval, and only then update this
manifest in a separate reviewed change. Never treat a source URL, stock image,
rendered/AI image, or damage diagram as evidence of an auction lot.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
# Immutable Git blob IDs of the existing auction records (NOT an approval for
# any additional record). A new/edited record must not deploy automatically.
FROZEN_SOURCE_BLOBS = {
    "research/owner-approved-japan-atp-sixth-30-archive-2026-11-21.json": "514b0527cc5bce969492180e9d6f935e7c63eda6",
    "research/owner-approved-japan-atp-fifth-30-archive-2026-11-20.json": "cc921c777e5c1d623015aa073a2628c66218f96c",
    "research/owner-approved-japan-atp-fourth-30-archive-2026-11-20.json": "74fdee9d9ab3d255530f5e0e114db5ac60bf6e00",
    "research/owner-approved-japan-atp-third-30-archive-2026-11-20.json": "3a84a714b4b5e1b06608841d23a2859d964a189b",
    "research/owner-approved-japan-atp-second-30-archive-2026-11-20.json": "cc35b52137d100c2215eb185c074b88b0cc9a993",
    "research/owner-approved-japan-atp-30-archive-2026-11-20.json": "e7fbb9e17470cf7a19634a54b0acd4d03259c8fa",
    "research/owner-approved-second-50-archive-2026-11-19.json": "8494df726f5f8d89d9b8b8a1226025e89e88d2aa",
    "research/owner-approved-50-archive-2026-11-19.json": "2d8962666cbc6750b5e3188b833d2a274ba4ea95",
    "research/owner-selected-japan-lots-2026-11-14.json": "f1113388a52405826c10a34d5b0f9e1f3236c7b6",
    "research/home-8-exact-lot-photo-sheet-references-2026-11-12.json": "c9dcb8545a9ec1b12249d7be8f5fe95009737c96",
    "data/gallery-lots.json": "32ba94fcda05cbff413083065a45c91e7341bfae",
    "data/approved-auction-lots.json": "75c851dbca8ca52b21aeb5cac737599a546bb788",
    "data/premium-real-auction-lots.json": "94e6457eaee345f8bcf39f9bfcc602c75fafb56d",
    "research/owner-approved-100-release-2026-11-15.json": "07541d6e76c6161d23b250aa3a053014b7cd7917",
}
# Whole-card fingerprints, not only image filenames: protect the exact photo,
# its matching auction sheet, mileage, auction data and visible description.
FROZEN_PREMIUM_CARD_FNV64 = (
    "a919fb16d0428ae4", "cf29d0c5c697ee01", "9b522e21d2abb1dc",
    "335ed22be3287e33", "c3cc3770b670d512", "44eaea108a07d572",
    "51cb1dff35a98916", "bdd3cc10b2992b06", "5e5d7adc020a5bf8",
    "d20c60b553a6f0de", "56f2513f6141a0f8", "c4bc734e596b3236",
)
CARD_RE = re.compile(r'<article\b[^>]*class="[^"]*\b(?:gallery-card|real-card)\b[^"]*"[^>]*>[\s\S]*?</article>', re.I)
PREMIUM_RE = re.compile(r'<article class="real-card"[^>]*>[\s\S]*?</article>')
VALID_IMAGE = re.compile(r'^/assets/(?:auction/(?:home|approved)|premium-auctions)/[a-zA-Z0-9._-]+\.(?:jpg|jpeg|png|webp)$', re.I)
BAD_ASSET_TERMS = re.compile(r'/(?:demo|visual|stock|street|illustration|anime|generated|ai-generated)/', re.I)


def _git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def _fnv_utf16(text: str) -> str:
    value = 0xcbf29ce484222325
    data = text.encode("utf-16-le")
    for offset in range(0, len(data), 2):
        codepoint_unit = data[offset] | (data[offset + 1] << 8)
        value = ((value ^ codepoint_unit) * 0x100000001b3) & 0xffffffffffffffff
    return f"{value:016x}"


def verify_frozen_inputs() -> None:
    """No new or modified car/photo/sheet/description without owner's review."""
    for relative, expected in FROZEN_SOURCE_BLOBS.items():
        path = ROOT / relative
        if not path.is_file() or _git_blob_id(path.read_bytes()) != expected:
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: source changed: " + relative)
    for name in ("premium-japan-korea.html", "premium-mobile-photo-demo.html"):
        path = ROOT / name
        cards = PREMIUM_RE.findall(path.read_text(encoding="utf-8"))
        if tuple(map(_fnv_utf16, cards)) != FROZEN_PREMIUM_CARD_FNV64:
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: auction card altered: " + name)


def _validate_card_links(card: str, page: str) -> None:
    for address in re.findall(r"""<a\b[^>]*\bhref=["']([^"']+)["']""", card, re.I):
        parsed = urlsplit(address.strip())
        # Auction cards may open ONLY self-hosted photos, sheets, internal
        # details, and the PapAuto lead form. Never send visitors to a seller.
        if address.startswith("//") or parsed.scheme or parsed.netloc:
            raise RuntimeError("PAPAUTO_NO_EXTERNAL_LINKS: " + page)
        if not address.startswith(("/", "#")):
            raise RuntimeError("PAPAUTO_NO_EXTERNAL_LINKS: invalid relative URL: " + page)
    for src in re.findall(r"""<img\b[^>]*\bsrc=["']([^"']+)["']""", card, re.I):
        if not VALID_IMAGE.fullmatch(src) or BAD_ASSET_TERMS.search(src):
            raise RuntimeError("PAPAUTO_AUCTION_ONLY: invalid card image: " + page)


def _valid_media(target: Path, asset: str) -> None:
    if not isinstance(asset, str) or not VALID_IMAGE.fullmatch(asset) or BAD_ASSET_TERMS.search(asset):
        raise RuntimeError("PAPAUTO_AUCTION_ONLY: non-auction image path")
    file = target / asset.lstrip("/")
    if not file.is_file() or file.is_symlink() or file.stat().st_size < 500:
        raise RuntimeError("PAPAUTO_PHOTO_REQUIRED: image file missing " + asset)
    header = file.read_bytes()[:12]
    if not (header.startswith(b"\xff\xd8\xff")
            or header.startswith(b"\x89PNG\r\n\x1a\n")
            or (header[:4] == b"RIFF" and header[8:12] == b"WEBP")):
        raise RuntimeError("PAPAUTO_PHOTO_REQUIRED: invalid image bytes " + asset)


def verify_published_output(target: Path) -> None:
    """Check every actually published gallery lot; not just the JS preview."""
    gallery = json.loads((target / "data/gallery-lots.json").read_text(encoding="utf-8"))
    rows = gallery.get("lots")
    if not isinstance(rows, list) or not rows or gallery.get("lot_count") != len(rows):
        raise RuntimeError("PAPAUTO_PHOTO_REQUIRED: invalid gallery registry")
    # Exactly 97 new + 3 already-published lots approved in the owner's
    # 100-page PDF review; the original 35 historic lots remain visible.
    receipt = json.loads(
        (ROOT / "research/owner-approved-100-release-2026-11-15.json")
        .read_text(encoding="utf-8")
    )
    approved_new = set(receipt["approved_new_owner_selected_ids"])
    approved_old = set(receipt["approved_existing_public_ids"])
    archive = json.loads((ROOT / "research/owner-approved-50-archive-2026-11-19.json").read_text(encoding="utf-8"))
    archive2 = json.loads((ROOT / "research/owner-approved-second-50-archive-2026-11-19.json").read_text(encoding="utf-8"))
    archive3 = json.loads((ROOT / "research/owner-approved-japan-atp-30-archive-2026-11-20.json").read_text(encoding="utf-8"))
    archive4 = json.loads((ROOT / "research/owner-approved-japan-atp-second-30-archive-2026-11-20.json").read_text(encoding="utf-8"))
    archive5 = json.loads((ROOT / "research/owner-approved-japan-atp-third-30-archive-2026-11-20.json").read_text(encoding="utf-8"))
    archive6 = json.loads((ROOT / "research/owner-approved-japan-atp-fourth-30-archive-2026-11-20.json").read_text(encoding="utf-8"))
    archive7 = json.loads((ROOT / "research/owner-approved-japan-atp-fifth-30-archive-2026-11-20.json").read_text(encoding="utf-8"))
    archive8 = json.loads((ROOT / "research/owner-approved-japan-atp-sixth-30-archive-2026-11-21.json").read_text(encoding="utf-8"))
    approved_archive = {r["id"] for r in archive["lots"] + archive2["lots"] + archive3["lots"] + archive4["lots"] + archive5["lots"] + archive6["lots"] + archive7["lots"] + archive8["lots"]}
    if (len(rows) != 412 or len(approved_archive) != 280 or len(approved_new) != 97 or len(approved_old) != 3
            or not (approved_new | approved_old | approved_archive).issubset({r["id"] for r in rows})
            or {r["id"] for r in rows if r["origin"] == "owner_selection"} != (approved_new | approved_archive)):
        raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: public lot set does not match owner-reviewed PDF")
    ids = set()
    for row in rows:
        ident = row.get("id")
        if not ident or ident in ids:
            raise RuntimeError("PAPAUTO_PHOTO_REQUIRED: duplicate/missing lot ID")
        ids.add(ident)
        if not isinstance(row.get("description"), str) or len(row["description"].strip()) < 30:
            raise RuntimeError("PAPAUTO_PHOTO_REQUIRED: missing description: " + ident)
        if type(row.get("mileage_km")) is not int or row["mileage_km"] < 0:
            raise RuntimeError("PAPAUTO_PHOTO_REQUIRED: missing mileage: " + ident)
        if not row.get("year") or not row.get("auction") or not row.get("lot_number"):
            raise RuntimeError("PAPAUTO_PHOTO_REQUIRED: missing auction details: " + ident)
        if ident in approved_archive and (row.get("rights_confirmed") is not False or row.get("status") != "reference_only" or len(row.get("photos",[]))!=2 or "Автомобиль не в наличии" not in row.get("description","")):
            raise RuntimeError("PAPAUTO_POLICY: archive reference misrepresented: " + ident)
        if row.get("inspection_kind") != "Аукционный лист":
            raise RuntimeError("PAPAUTO_AUCTION_ONLY: diagram is not auction sheet: " + ident)
        photos = row.get("photos") or []
        sheet = row.get("inspection_image")
        if not isinstance(photos, list) or not photos or not sheet:
            raise RuntimeError("PAPAUTO_PHOTO_REQUIRED: photo and sheet mandatory: " + ident)
        for asset in photos + [sheet]:
            _valid_media(target, asset)
        # Source links, competitor URLs and "visit original listing" are
        # private research data only and must not appear in public JSON.
        if any(k in row for k in ("source_url", "source_listing", "listing_url", "photo_url", "sheet_url")):
            raise RuntimeError("PAPAUTO_NO_EXTERNAL_LINKS: source leaked: " + ident)
    gallery_html = (target / "gallery.html").read_text(encoding="utf-8")
    cards = CARD_RE.findall(gallery_html)
    cards = [c for c in cards if "gallery-card" in c.split(">", 1)[0]]
    if len(cards) != len(rows):
        raise RuntimeError("PAPAUTO_PHOTO_REQUIRED: gallery HTML card count mismatch")
    for card in cards:
        _validate_card_links(card, "gallery.html")
        if not all(x in card for x in ("gallery-card-photo", "gallery-thumb", "gallery-description", "Пробег", "Аукционный лист")):
            raise RuntimeError("PAPAUTO_PHOTO_REQUIRED: incomplete gallery card")
    for page in ("premium-japan-korea.html", "premium-mobile-photo-demo.html"):
        html = (target / page).read_text(encoding="utf-8")
        if "data-selection-grid" in html or 'id="market-catalog"' in html:
            raise RuntimeError("PAPAUTO_PHOTO_REQUIRED: text-only catalog resurfaced")
        premium_cards = PREMIUM_RE.findall(html)
        if len(premium_cards) != 11:
            raise RuntimeError("PAPAUTO_PHOTO_REQUIRED: unexpected premium card count")
        for card in premium_cards:
            _validate_card_links(card, page)
            if not all(x in card for x in ("real-img-main", "real-img-sheet", "real-trim", "<span>Пробег</span>")):
                raise RuntimeError("PAPAUTO_PHOTO_REQUIRED: incomplete premium auction card")
    print("PAPAUTO_RELEASE_CONTRACT_OK: frozen approved lots, self-hosted media, no outbound auction links")


if __name__ == "__main__":
    verify_frozen_inputs()
