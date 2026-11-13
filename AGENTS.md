# PapAuto — instructions for all future agents

MANDATORY: Read docs/AUCTION_ONLY_GALLERY.md before changing car galleries, photographs, auction media imports, manifests or media policy tests.

The user's permanent absolute rule is: ONLY REAL AUCTION PHOTOS of the EXACT lot + authentic matching FULL AUCTION SHEET + truthful description and lot data. NEVER generic/street/dealer/showroom/stock/AI/marketing/parking/port/warehouse photos, not even placeholders. Do not resurrect deleted image sources. Do not invent sheets, lot numbers, mileage, grades, prices or permissions. Never link customers to competitors.

New media requires image-by-image exact-lot provenance, the matching full auction sheet, verified written rights for commercial reuse and self-hosting of both photos and sheet, and all fail-closed importer checks. Store unresolved leads only in research/, not public data/assets. Goal of 500 is not permission to fabricate. Preserve already-published historical cards but do not claim all archival photo rights are licensed.

Read scripts/import_auction_photos.py, tests/test_auction_only_images_policy.py and tests/test_auction_media_policy.py. Run project CI and mobile browser tests before deployment.
