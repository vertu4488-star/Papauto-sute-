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

Owner instruction 2026-11-20: the exact separate preview of 30 additional Chinese-market supplier examples explicitly approved for china-order.html. These are not auction listings or verified reduced-fee cars. No third-party license is asserted. Only the third batch of 30 fixed digests in verify_china_order_release.py is newly allowed, alongside the previous 79; auction safeguards unchanged. Includes the five previously previewed distinct models only as part of this approved batch.

Owner instruction 2026-11-20: the exact separate preview of 30 additional Chinese-market supplier examples explicitly approved for china-order.html. These are not auction listings or verified reduced-fee cars. No third-party license is asserted. Only the fourth batch of 30 fixed digests in verify_china_order_release.py is newly allowed, alongside the previous 109; auction safeguards unchanged.

Owner instruction 2026-11-20: the exact separate preview of 30 additional Chinese-market supplier examples explicitly approved for china-order.html. These are not auction listings or verified reduced-fee cars. No third-party license is asserted. Only the fifth batch of 30 fixed digests in verify_china_order_release.py is newly allowed, alongside the previous 139; auction safeguards unchanged.

Owner instruction 2026-11-20: exact 30 additional power-listed supplier examples approved for china-order.html. Only the fixed sixth batch digests are allowed alongside previous 169. Supplier-listed <=160 PS is not document-verified power or a reduced-fee guarantee. Starting prices are NOT FOB. Auction safeguards unchanged; no license asserted.

Owner instruction 2026-11-20: exact 11 additional power-listed supplier examples approved for china-order.html. Only the fixed seventh batch digests are allowed alongside previous 199. Supplier-listed <=160 PS is not document-verified power or a reduced-fee guarantee. Starting prices are NOT FOB. Auction safeguards unchanged; no license asserted.

Owner instruction 2026-11-20: exact 10 additional power-listed supplier examples approved for china-order.html. Only the fixed eighth batch digests are allowed alongside previous 210. Supplier-listed <=160 PS is not document-verified power or a reduced-fee guarantee. Starting prices are NOT FOB. Auction safeguards unchanged; no license asserted.

Owner instruction 2026-11-20: exact nine GoldenLane source-linked supplier examples approved for china-order.html. Only fixed ninth-batch digests permitted after validation; no license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.

Owner instruction 2026-11-20: exact 30 supplier examples shown in PapAuto_30_China_review.pdf expressly approved for china-order.html. Only fixed tenth-batch digests permitted, 19 GoldenLane and 11 EZ Auto Global. No license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.

Owner instruction 2026-11-20: exact 30 supplier examples shown in PapAuto_China_30_batch11.pdf expressly approved for china-order.html. Only fixed eleventh-batch digests permitted, 28 Xin Che Hang and 2 China Used Car. No license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.

Owner instruction 2026-11-20: exact 30 supplier examples shown in PapAuto_China_30_batch12.pdf expressly approved for china-order.html. Only fixed twelfth-batch digests permitted, 30 Xin Che Hang. No license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.

Owner instruction 2026-11-20: exact 30 supplier examples shown in PapAuto_China_30_batch13.pdf expressly approved for china-order.html. Only fixed thirteenth-batch digests permitted, 30 Xin Che Hang. No license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.

Owner instruction 2026-11-20: exact 30 supplier examples shown in PapAuto_China_30_batch14.pdf expressly approved for china-order.html. Only fixed fourteenth-batch digests permitted, 30 Xin Che Hang. No license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.

Owner instruction 2026-11-20: exact 30 supplier examples shown in PapAuto_China_30_batch15.pdf expressly approved for china-order.html. Only fixed fifteenth-batch digests permitted, 30 Xin Che Hang. No license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.

Owner instruction 2026-11-20: exact 30 supplier examples shown in PapAuto_China_30_batch16.pdf expressly approved for china-order.html. Only fixed sixteenth-batch digests permitted, 30 Xin Che Hang. No license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.

Owner instruction 2026-11-20: exact 30 supplier examples shown in PapAuto_China_30_batch17.pdf expressly approved for china-order.html. Only fixed seventeenth-batch digests permitted, 30 Xin Che Hang. No license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.

Owner instruction 2026-11-20: exact 30 supplier examples shown in PapAuto_China_30_batch18.pdf expressly approved for china-order.html. Only fixed eighteenth-batch digests permitted, 30 Xin Che Hang. No license assertion, no auction claims, no verified power or reduced-fee claims. Auction safeguards unchanged.

Owner instruction 2026-11-20: exactly the 30 ATP archival examples from PapAuto_Japan_30_ATP_review.pdf authorized after review, receipt research/owner-approved-japan-atp-30-archive-2026-11-20.json. Only exact ninety frozen media digests; no third-party license assertion, no current stock claims, ordinary auction protections unchanged.

Owner instruction 2026-11-20: exactly the 30 ATP archival examples from PapAuto_Japan_30_ATP_batch2_review.pdf authorized after review, receipt research/owner-approved-japan-atp-second-30-archive-2026-11-20.json. Only exact ninety frozen media digests; no third-party license assertion, no current stock claims, ordinary auction protections unchanged.

Owner instruction 2026-11-20: exactly the 30 ATP archival examples from PapAuto_Japan_30_ATP_batch3_review.pdf authorized after review, receipt research/owner-approved-japan-atp-third-30-archive-2026-11-20.json. Only exact ninety frozen media digests; no third-party license assertion, no current stock claims, ordinary auction protections unchanged.

Owner instruction 2026-11-20: exactly the 30 ATP archival examples from PapAuto_Japan_30_ATP_batch4_cards.zip authorized after review, receipt research/owner-approved-japan-atp-fourth-30-archive-2026-11-20.json. Only exact ninety frozen media digests; no third-party license assertion, no current stock claims, ordinary auction protections unchanged.
