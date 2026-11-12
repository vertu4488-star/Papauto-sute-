# PapAuto — mandatory auction-only photograph policy

**User decision (2026-11-12): NEVER publish or reintroduce ordinary street photographs, stock/catalogue pictures, Wikimedia Commons CC0 / Creative Commons car portraits, random marketplace photos, AI-generated vehicle card images, or general illustration galleries.** This instruction supersedes previous photo-gallery development requests.

## Allowed media
- Publish vehicle photographs **only** when they are linked to a specific, verifiable auction lot, together with its genuine auction sheet or inspected lot documentation. Use exactly that lot's original photos, not another car of the same model.
- Store verified auction images on PapAuto's own host under `/assets/auction/home/` or `/assets/premium-auctions/`, with traceable provenance and reuse rights. Never link customers to external auction marketplaces.
- An auction illustration or damage diagram must be explicitly labeled; never call it an original auction sheet.
- China, Korea, and Japan model directories without proven auction photos remain TEXT ONLY (no image, dummy placeholders depicting vehicles, gallery tiles, mixed-model photos, or fake sales data). Keep the searchable models and inquiry routes.

## Forbidden origins and import code
- Do not recreate `assets/demo/`, `research/cc0-photo-provenance.json`, `research/approved-cc0-vehicle-sources.json`, `scripts/import_cc0_vehicle_images.py`, `scripts/discover_and_expand_cc0_catalog.py`, their related GitHub workflows, or any replacement importer that downloads non-auction car photos.
- Do not use `assets/visual/*.webp` as a vehicle image. The homepage and premium hero must use an actual source-linked auction-lot photo, not a generic graphic.
- Korean vehicle listing advertisements (Autowini etc.) are not automatically auction lots. They must not be presented as auction-photo cards without auction identity and paperwork.
- This is enforced in `scripts/build_static_public.py` and `tests/test_auction_only_images_policy.py`. Do not weaken the checks. All source edits must preserve `npm/JS` checks, link safety and user forms.

## Before publishing
1. Confirm source lot identity, auction name/date/number, original photos and sheet, and rights.
2. Verify photographs correspond to the exact car, and no unlicensed or street photos appear in rendered HTML/JS/CSS/data.
3. Run the predeploy suite, static public build, and Chromium mobile QA.
4. Check the actual Render result and `https://papauto.ru` after clearing Cloudflare cache.
5. Do not confuse 135 **model names** with 135 photo-backed auction lots.

Deletion from the current Git branch and CDN does **not** remove historical Git objects or historical external archives; never promise that it does.
