# PapAuto — instructions for all future agents

MANDATORY: Read docs/AUCTION_ONLY_GALLERY.md before changing car galleries, photographs, auction media imports, manifests or media policy tests.

The user's permanent absolute rule is: ONLY REAL AUCTION PHOTOS of the EXACT lot + authentic matching FULL AUCTION SHEET + truthful description and lot data. NEVER generic/street/dealer/showroom/stock/AI/marketing/parking/port/warehouse photos, not even placeholders. Do not resurrect deleted image sources. Do not invent sheets, lot numbers, mileage, grades, prices or permissions. Never link customers to competitors.

New media requires image-by-image exact-lot provenance, the matching full auction sheet, verified written rights for commercial reuse and self-hosting of both photos and sheet, and all fail-closed importer checks. Store unresolved leads only in research/, not public data/assets. Goal of 500 is not permission to fabricate. Preserve already-published historical cards but do not claim all archival photo rights are licensed.

Read scripts/import_auction_photos.py, tests/test_auction_only_images_policy.py and tests/test_auction_media_policy.py. Run project CI and mobile browser tests before deployment.

The owner expressly directed publication of the 100 lots in research/owner-selected-japan-lots-2026-11-14.json on 2026-11-14. Only that batch is published on the basis of that instruction. Do not describe the batch as licensed. The ordinary import requirements apply to subsequent additions.

Owner instruction 2026-11-19: exactly the 50 reviewed Japan archival reference records in research/owner-approved-50-archive-2026-11-19.json were authorized explicitly under the owner’s responsibility. This is not a third-party license; rights_confirmed stays false. No general exception, no street or unrelated photos, no missing sheets, no external card links, and no available-for-sale claims. Ordinary importer rights requirements remain in force for any other batch.

Owner instruction 2026-11-19, second batch: exactly the 50 cards in research/owner-approved-second-50-archive-2026-11-19.json approved after PDF/JPG presentation. No general release exception and no third-party license assertion. Keep all original photo, sheet and no-street-photo safeguards.

## Permanent China sourcing watchlist (owner instruction 2026-11-20)
Use `research/china-util-model-watchlist.json` as the standing model-by-model sourcing queue: all 96 candidate model families on the China market, grouped by brand origin, and 9 ordinary-tariff families. Keep China purchase market distinct from brand origin (Chinese, Japanese, Korean, European). Prioritize gasoline ICE up to 2000 cc and 117.68 kW, actual 2022–2023 production dates where practical, and exact documented power, current rules and export eligibility. The power and engine hints are unverified, not vehicle facts. Keep hybrids/EV separate until rated power is verified. Search for at least one complete exact-lot photo+matching original inspection document per family, sharp natural background, no watermark, no street or generic photos. Never mark a candidate as a verified reduced-fee vehicle or publish a photo lot merely because the family is on this list. Preserve all release safeguards above.

Owner instruction 2026-11-20: exact 49 previously displayed Xin Che Hang supplier examples explicitly approved for separate China-order section under owner responsibility. This is NOT an auction listing or a third-party license. Only immutable photo set verified by scripts/verify_china_order_release.py is allowed on china-order.html; rights_confirmed remains false, report and documented power unverified. No additional exception or alteration of auction policy. No competitor links or live-stock claims.

Owner instruction 2026-11-20: the exact separate preview of 30 additional Chinese-market supplier examples explicitly approved for china-order.html. These are not auction listings or verified reduced-fee cars. No third-party license is asserted. Only the 30 fixed digests in verify_china_order_release.py are newly allowed, alongside the previous 49; auction safeguards unchanged. The separate five-card preview is not included in this release.
