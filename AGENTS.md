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

Owner instruction 2026-11-20: exactly the 30 ATP archival examples from PapAuto_Japan_30_ATP_batch5_cards.zip authorized after review, receipt research/owner-approved-japan-atp-fifth-30-archive-2026-11-20.json. Only exact ninety frozen media digests; no third-party license assertion, no current stock claims, ordinary auction protections unchanged.

Owner instruction 2026-11-21: exactly the 30 ATP archival examples from PapAuto_Japan_30_auction_cards_review_2026-11-21.pdf authorized after review, receipt research/owner-approved-japan-atp-sixth-30-archive-2026-11-21.json. Only exact ninety frozen media digests; no third-party license assertion, no current stock claims, ordinary auction protections unchanged.

Owner instruction 2026-11-21: select and add missing model-year Japanese auction examples in the Drom 991 project. Exactly 17 source photo+full-sheet pairs reviewed; source file research/owner-approved-japan-drom991-gap-17-archive-2026-11-21.json. Fifty-one immutable JPEGs; rounded source mileage, no current inventory, no commercial media license assertion. Ordinary auction-only release restrictions remain active.

Owner approved on 2026-11-21 exactly 30 Japan auction photo+sheet pairs in PapAuto_Japan_Next30_Drom991_2026-11-21.pdf. Receipt research/owner-approved-japan-next30-2026-11-21.json. Ninety exact JPEGs; SHA256 of source manifests and owner-reviewed media frozen. Archive references only, no real-time stock and no implied third-party media license. Normal gallery approval and media quality rules still apply.

Owner directed on 2026-11-21 another 30 archival Japan auction photo+sheet records. Source-reviewed PDF PapAuto_Japan_Another30_489_2026-11-21.pdf, receipt research/owner-approved-japan-followup30-2026-11-21.json. Ninety immutable JPEGs, all matching complete auction sheets. Statistics only, no inventory or third-party license assertion. All normal image-only release restrictions preserved.

On 2026-11-21, the owner explicitly approved the exact PapAuto_Japan_Another30_519_2026-11-21.pdf collection for an archival-only 30-card Japanese publication. Source-frozen receipt: research/owner-approved-japan-next30-519-2026-11-21.json. No street photos, no third-party commercial rights assertion, no dealer/competitor links or live inventory claims.

On 2026-11-21, user expressly approved 30 original photo/full-sheet Japan archive records in PapAuto_Japan_Another30_549_2026-11-21.pdf to be published after the previously approved 519 release. Receipt: research/owner-approved-japan-next30-549-2026-11-21.json. No unrelated or missing photos, no stock/real-time sales claims, rights_confirmed=false. All auction-only restrictions remain.

Owner expressly approved on 2026-11-21 exactly 30 full-sheet Japanese historic auction records in PapAuto_Japan_Another30_579_2026-11-21.pdf. New immutable receipt: research/owner-approved-japan-next30-579-2026-11-21.json. Exactly 90 JPEGs, 30 source auction lots; no street/dealer photos; no external card links, stock claims or third-party rights assertion. This is not blanket permission for any other batch.

Owner expressly approved on 2026-11-21 exactly 30 full-sheet Japanese historic auction records in PapAuto_Japan_Another30_609_2026-11-21.pdf. New immutable receipt: research/owner-approved-japan-next30-609-2026-11-21.json. Exactly 90 JPEGs, 30 source auction lots; no street/dealer photos; no external card links, stock claims or third-party rights assertion. This is not blanket permission for any other batch.

Owner expressly approved on 2026-11-21 exactly 30 full-sheet Japanese historic auction records in PapAuto_Japan_Another30_639_2026-11-21.pdf. New immutable receipt: research/owner-approved-japan-next30-639-2026-11-21.json. Exactly 90 JPEGs, 30 source auction lots; no street/dealer photos; no external card links, stock claims or third-party rights assertion. This is not blanket permission for any other batch.

Owner approved the exact PDF PapAuto_Japan_18_ATP_review_2026-11-25.pdf and explicitly requested publication. Exact 18 archived source examples / 54 frozen JPEGs only; research/owner-approved-japan-gap18-2026-11-25.json. No commercial license assertion, no live inventory, no general exception for other records.

Owner approved the exact PDF PapAuto_Honda_7_ATP_review_2026-11-25.pdf and explicitly requested publication. Exact 7 archived source examples / 21 frozen JPEGs only; research/owner-approved-japan-honda7-2026-11-25.json. No commercial license assertion, no live inventory, no general exception for other records.


Owner release instruction 2026-11-26: exactly the 33 visually reviewed SEO reference cards in PapAuto_ATP_33_SEO_cards_preview.zip (manifest SHA256 6a82e9ffd6d14a42759982180357b69330bff49a5be2245ba159b4668435cc5a) are approved for separate model-page reference display. The original 66 files are pinned by aggregate digest in scripts/render_atp33_references.py. Not new auction inventory, no assertion of sale or license; source attribution remains, no outbound supplier links, no revoked images. All other auction registry safeguards and existing 666 lots remain unchanged. No supplier outreach requested.


Owner instruction 2026-11-26: publish only nine individually reviewed ATP Japan reference examples in frozen manifest SHA256 857fb42c8b651403ad44a11e0bcd459caf790a4c20d734e4b82d714d2962630d, numbers 1,2,3,7,8,10,11,12,13, with 27 original files. Keep separate from 666-lot gallery, no license or availability claim; do not publish numbers 4,6,9 (missing full sheet or street photos) or 5 (not found). Exact source/lot/price attribution and duplicate checks required. No supplier outreach.

Owner expressly approved on 2026-11-26 the exact five cards shown in PapAuto_Honda_ATP_5_cards_2026-11-26.pdf, and then explicitly requested Render publication. Receipt research/owner-reviewed-honda-atp-5-20261126.json pins 15 original JPEG SHA256 digests and the reviewed PDF digest. Separate historical SEO model references only; no claim of third-party license or available stock; no new gallery lots, no other exceptions, no external supplier links. All other release safeguards unchanged. Hybrid Freed Spike examples are archive only, not a direct import offer.

Owner explicitly approved publication on 2026-11-26 of exactly the 30 cards from PapAuto_Japan_ATP_30_batch1_2026-11-26.pdf (SHA256 14aa4de9c311d2dc6078e4c18604ca6df749a47aba9b64ba5ac3846b8cc19e34). The release pins source artifact 15115707921, frozen manifest and exact ordered rows; exactly two photos and one full sheet per reviewed lot, source attribution, archival SEO examples only, no live stock, no third-party license assertion, no outbound supplier links, no other batch approved. Existing public gallery remains unchanged. Any duplicate must be reused, never duplicated.

Owner explicitly approved publication of exactly 30 cards from PapAuto_Japan_ATP_30_batch2_2026-11-26.pdf on 2026-11-26 (SHA256 d03bf7cb40dec3b3a0da67ea9c1aa5ca77f4ff70b180d02ee8d3e17cef20c617). Frozen selection digest 9d9611a7c8f39c9286af6a4cf6ab0a81d6ba16590919e120c2c735165c60eef1, source artifact 15115707921. Two original photos and one complete sheet per lot; no batch 1 duplicates, no supplier links, no assertion of third-party media license, no stock claims. Archival SEO references only, gallery remains unchanged. Approval does not extend to the remaining 15.


## Постоянное правило публичных подписей (28.11.2026)
Запрещено использовать слово «иллюстрация» и его формы в публичных текстах, ALT и карточках. Использовать точные нейтральные подписи, не выдавая условное изображение за фото конкретного автомобиля. Для карточек действует прежний абсолютный запрет на ИИ/стоковые/несоответствующие фотографии, без исключений. Проверка терминологии входит в сборку Render; замороженные данные и подлинные фото не менять.


Owner approval 2026-11-28: exactly four generated promotional WebP visuals for the homepage informational service cards (turnkey, no Russian mileage, individual selection, delivery). They are not actual customers, completed orders or auction lot photographs; never use them in galleries, listings, models, auction sheets or sale statistics. Their fixed hashes and scope are checked by the static build. No other change to the auction photo policy.
