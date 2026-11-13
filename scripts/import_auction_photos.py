#!/usr/bin/env python3
"""Import authorized AUCTION PHOTOS into PapAuto's self-hosted public catalog.

No remote downloading, scraping or fetching: files must already have been legally
obtained and explicitly licensed for commercial self-hosting.

Usage: python scripts/import_auction_photos.py --intake PATH --media-dir DIR

The intake document is a JSON object {"lots": [...]} with per-lot fields:
 id, country, make, model, year, photos (relative local filenames), auction_sheet (relative filename), rights:
 {holder, evidence_reference, commercial_use, self_host};
 optionally lot, auction, body, color, mileage_km, grade,
 sale_status, sold_date, sold_price, currency, sale_evidence_reference,
 vehicle_evidence_reference, source_url (private only).

Creates local copies in assets/auction/approved/, public
data/approved-auction-lots.json and a private rights log in research/.
Run project tests and commit the generated files before deployment.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "auction" / "approved"
PUBLIC = ROOT / "data" / "approved-auction-lots.json"
PRIVATE = ROOT / "research" / "auction-photo-rights-ledger.json"
COUNTRIES = {"japan", "south-korea", "china"}
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
CURRENCIES = {"japan": "JPY", "south-korea": "KRW", "china": "CNY"}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def image_format(data):
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    raise ValueError("Unsupported image content: need a JPEG, PNG or WebP")


def normalize_lot(row, media_dir):
    key = str(row.get("id") or "")
    require(bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{2,75}", key)), "Invalid lot ID")
    country = row.get("country")
    require(country in COUNTRIES, f"{key}: invalid country")
    require(row.get("make") and row.get("model"), f"{key}: make/model needed")
    year = int(row.get("year", 0))
    require(1950 <= year <= date.today().year + 1, f"{key}: invalid year")

    rights = row.get("rights") or {}
    require(bool(rights.get("holder")), f"{key}: missing rights holder")
    require(bool(rights.get("evidence_reference")), f"{key}: missing license evidence reference")
    require(rights.get("commercial_use") is True, f"{key}: commercial license required")
    require(rights.get("self_host") is True, f"{key}: self-hosting permission required")
    require(bool(row.get("vehicle_evidence_reference")), f"{key}: missing lot-to-photo provenance")
    description = str(row.get("description") or "").strip()
    require(len(description) >= 30, f"{key}: verified description (30+ characters) required")
    require(bool(row.get("auction")) and bool(row.get("lot")),
            f"{key}: auction house and specific lot number required")
    auction_date = str(row.get("auction_date") or "")
    try:
        date.fromisoformat(auction_date)
    except ValueError as exc:
        raise ValueError(f"{key}: valid YYYY-MM-DD auction date required") from exc
    require(str(row.get("grade") or "").strip(), f"{key}: actual auction grade required")
    require(isinstance(row.get("mileage_km"), int)
            and 0 <= row["mileage_km"] <= 2_000_000,
            f"{key}: verified integer mileage_km required")
    require(row.get("photo_context") == "original_auction_lot",
            f"{key}: street/showroom/generic photo refused")

    photos = row.get("photos")
    require(isinstance(photos, list) and 1 <= len(photos) <= 15, f"{key}: 1-15 images required")
    provenance = row.get("photo_evidence")
    require(isinstance(provenance, list) and len(provenance) == len(photos),
            f"{key}: specific source evidence required for every photo")
    binaries = []
    for i, path in enumerate(photos, 1):
        proof = provenance[i - 1]
        require(isinstance(proof, dict)
                and proof.get("file") == path
                and proof.get("capture_type") == "auction_house_lot_photo"
                and proof.get("auction") == row.get("auction")
                and str(proof.get("lot")) == str(row.get("lot"))
                and proof.get("auction_date") == auction_date
                and bool(proof.get("proof_reference")),
                f"{key}: photo {i} not proven to match original auction lot")
        require(isinstance(path, str) and len(path) < 255, f"{key}: invalid photo path")
        rel = Path(path)
        require(not rel.is_absolute() and ".." not in rel.parts and rel.suffix.lower() in ALLOWED_EXT,
                f"{key}: unsafe file path: {path}")
        full = (media_dir / rel).resolve()
        require(full.is_relative_to(media_dir.resolve()), f"{key}: unsafe source path")
        require(full.is_file(), f"{key}: missing source photo: {path}")
        require(not full.is_symlink(), f"{key}: symlink photo refused")
        data = full.read_bytes()
        require(2048 <= len(data) <= 15 * 1024 * 1024, f"{key}: photo too small or large: {path}")
        fmt = image_format(data)
        sha = hashlib.sha256(data).hexdigest()
        name = f"{key}-{i:02d}-{sha[:12]}{fmt}"
        binaries.append((name, data, sha))

    # The auction inspection sheet is a separate, authentic, locally hosted image.
    # Permission for ordinary vehicle photographs is not permission for a scanned sheet.
    require(rights.get("sheet_commercial_use") is True, f"{key}: auction sheet commercial rights required")
    require(rights.get("sheet_self_host") is True, f"{key}: auction sheet self-host permission required")
    sheet_evidence = row.get("sheet_evidence")
    require(isinstance(sheet_evidence, dict)
            and sheet_evidence.get("document_type") == "original_auction_sheet"
            and sheet_evidence.get("auction") == row.get("auction")
            and str(sheet_evidence.get("lot")) == str(row.get("lot"))
            and sheet_evidence.get("auction_date") == auction_date
            and bool(sheet_evidence.get("proof_reference")),
            f"{key}: genuine matching FULL auction sheet required")
    source_sheet = row.get("auction_sheet")
    require(sheet_evidence.get("file") == source_sheet,
            f"{key}: sheet provenance filename mismatch")
    require(isinstance(source_sheet, str) and len(source_sheet) < 255, f"{key}: auction sheet required")
    sheet_rel = Path(source_sheet)
    require(not sheet_rel.is_absolute() and ".." not in sheet_rel.parts
            and sheet_rel.suffix.lower() in ALLOWED_EXT, f"{key}: unsafe auction sheet path")
    sheet_path = (media_dir / sheet_rel).resolve()
    require(sheet_path.is_relative_to(media_dir.resolve())
            and sheet_path.is_file() and not sheet_path.is_symlink(), f"{key}: auction sheet is missing")
    sheet_data = sheet_path.read_bytes()
    require(2048 <= len(sheet_data) <= 15 * 1024 * 1024, f"{key}: auction sheet size not allowed")
    sheet_format = image_format(sheet_data)
    sheet_hash = hashlib.sha256(sheet_data).hexdigest()
    sheet_name = f"{key}-sheet-{sheet_hash[:12]}{sheet_format}"
    binaries.append((sheet_name, sheet_data, sheet_hash))
    require(len({h for _, _, h in binaries}) == len(binaries),
            f"{key}: duplicate photo or sheet bytes")

    status = row.get("sale_status", "reference_only")
    require(status in {"reference_only", "verified_sold"}, f"{key}: invalid sale status")
    if status == "verified_sold":
        require(bool(row.get("sale_evidence_reference")), f"{key}: sold evidence missing")
        require(bool(row.get("sold_date")), f"{key}: sale date missing")
        require(row.get("currency") == CURRENCIES[country], f"{key}: incorrect sale currency")
        require(isinstance(row.get("sold_price"), (float, int))
                and row["sold_price"] > 0, f"{key}: final price missing")

    public = {
        "id": key, "country": country,
        "make": str(row["make"]).strip()[:80], "model": str(row["model"]).strip()[:120],
        "year": year,
        "photos": [f"/assets/auction/approved/{name}" for name, _, _ in binaries[:-1]],
        "auction_sheet": f"/assets/auction/approved/{sheet_name}",
        "description": description[:1200],
        "photo_context": "original_auction_lot",
        "sheet_type": "original_auction_sheet",
        "sheet_permission": True,
        "image_rights": "approved",
        "rights_holder": str(rights["holder"]),
        "rights_reference": str(rights["evidence_reference"]),
        "commercial_use_permission": True,
        "self_host_permission": True,
        "vehicle_evidence_reference": str(row["vehicle_evidence_reference"]),
        "sale_status": status
    }
    for field in ("body", "color", "grade", "auction", "lot", "mileage_km",
                  "auction_date", "trim", "engine", "engine_cc", "transmission",
                  "inspector_notes", "fuel_type", "steering", "power_hp"):
        if row.get(field) is not None:
            public[field] = row[field]
    if status == "verified_sold":
        for field in ("sold_date", "sold_price", "currency", "sale_evidence_reference"):
            public[field] = row[field]
    private = {
        "id": key, "photo_sha256": [sha for _, _, sha in binaries],
        "source_url": row.get("source_url"),
        "original_photo_files": photos,
        "original_auction_sheet_file": source_sheet,
        "license_evidence": rights["evidence_reference"],
        "license_holder": rights["holder"],
        "checked_on": date.today().isoformat()
    }
    return public, private, binaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intake", type=Path, required=True)
    parser.add_argument("--media-dir", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    media_dir = args.media_dir.resolve()
    doc = json.loads(args.intake.read_text(encoding="utf-8"))
    lots = doc.get("lots", [])
    require(isinstance(lots, list) and lots, "Intake lots must be a nonempty array")
    require(len(lots) <= 1000, "Maximum 1000 lots per import")
    current = json.loads(PUBLIC.read_text(encoding="utf-8"))
    existing = current.get("lots", [])
    require(isinstance(existing, list), "Invalid public catalog")
    registry = {r["id"]: r for r in existing}
    base_gallery = json.loads((ROOT / "data" / "gallery-lots.json").read_text(encoding="utf-8"))
    base_ids = {record["id"] for record in base_gallery["lots"]}
    require(len(base_ids) == 37, "37 full-sheet source auction lot IDs expected")
    ledger = json.loads(PRIVATE.read_text(encoding="utf-8")) if PRIVATE.exists() else {"lots": []}
    history = {r["id"]: r for r in ledger.get("lots", [])}
    binaries = []
    seen = set()
    known_media_hashes = {digest: lot_id for lot_id, row in history.items()
                          for digest in row.get("photo_sha256", [])}
    new_media_hashes = {}
    for row in lots:
        public, private, files = normalize_lot(row, media_dir)
        require(public["id"] not in seen and public["id"] not in base_ids,
                "Duplicate lot ID in batch or already published base gallery")
        seen.add(public["id"])
        for name, data, digest in files:
            require(known_media_hashes.get(digest) in {None, public["id"]}
                    and new_media_hashes.get(digest) in {None, public["id"]},
                    f"{public['id']}: identical photo/sheet reused across different lots")
            new_media_hashes[digest] = public["id"]
        registry[public["id"]] = public
        history[public["id"]] = private
        binaries.extend(files)
    require(len(registry) + len(base_ids) <= 500,
            "500-card catalogue ceiling reached; extra rows cannot silently inflate the count")
    if args.dry_run:
        print(f"Validated {len(seen)} lots / {len(binaries)} photos; no changes written.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    PRIVATE.parent.mkdir(parents=True, exist_ok=True)
    for name, data, _ in binaries:
        dest = OUT_DIR / name
        if dest.exists():
            require(dest.read_bytes() == data, f"File collision at {name}")
        else:
            dest.write_bytes(data)
    current["updated_at"] = date.today().isoformat()
    current["lots"] = sorted(registry.values(), key=lambda r: r["id"])
    PRIVATE.write_text(json.dumps({"lots": sorted(history.values(), key=lambda r: r["id"])},
                                 ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PUBLIC.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(f"Imported {len(seen)} licensed lots and {len(binaries)} self-hosted images (photos and auction sheets).")
    print("Run: python -m unittest discover -s tests -p test_auction_media_policy.py")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"Import stopped safely: {exc}", file=sys.stderr)
        sys.exit(1)
