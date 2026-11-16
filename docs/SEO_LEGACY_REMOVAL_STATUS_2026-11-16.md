# SEO removal tracker — papauto.ru

**Date:** 2026-11-16
**Historical URL inventory:** docs/SEO_LEGACY_URL_INVENTORY_2026-11-15.md

## Completed

- Historical candidate paths inventoried: **22**; compared with active sitemaps, with no overlapping active URLs. This is an archive sample, not a complete count of indexed pages.
- IndexNow notifications on 2026-11-15: **20** retired URLs, accepted by OpenSEO for submission.
- Additional IndexNow notifications on 2026-11-16: **2** remaining legacy endpoints, status **submitted**. Total notified: **22**. Notification is not proof of search removal.
- Site's current sitemap remains intact: 52 canonical pages in sitemap.xml plus 133 lots in generated sitemap-lots.xml.
- An email request with the full historical path list was sent to **webmaster@support.yandex.ru** on 2026-11-16 asking to exclude old URLs and restore the page-removal tool.
- Sample legacy pages previously observed HTTP 404, e.g. `/kontakty`, `/shop/katalog-tovarov`, `/stajling-ford-kuga`. Not every historical URL has been live-tested for its HTTP response.
- Six sample legacy URLs were inspected through connected Google Search Console on 2026-11-16; all six returned **URL is unknown to Google**. This does not prove the state of the full historical inventory.

## Blocker / outstanding

- Yandex Webmaster access to the owned domain was confirmed, but the **Tools → Removal of pages from search** tool returned a 404 in the 2026-11-16 browser session. No removal requests were confirmed through that form.
- Yandex Webmaster's **Crawl Statistics** tool and summary updates were temporarily unavailable, so current index counts and legacy-results inventory could not be verified.
- Wait for or monitor Yandex support response. Once the removal tool is available, submit **only** retired URLs that remain in Yandex results; avoid removing the entire site or active directories.
- Verify HTTP 404/410 for every retired URL and 301 www→apex; keep current pages and canonical sitemap accessible.
- Track actual removals from Yandex / Google separately. Keep old URLs off current sitemaps and do not reintroduce retired page content.

## Safety

**DO NOT submit live/current URLs for deletion.** The active site, current sitemap pages, lead forms, and canonical homepage must remain indexable. Google does not use IndexNow; submitting an IndexNow notification does not delete Google search results.
