# Incident regressions — 2026-11-15

## External analytics TLS in local visual QA

Run 43581781457 failed with ERR_CERT_AUTHORITY_INVALID while loading the local gallery. Local pages load live Metrica and GA scripts through metrika.js. Their network/TLS availability must not decide a local layout test or send synthetic visits to live analytics.

Local visual QA now substitutes only the two exact analytics hosts used by metrika.js. TLS verification and error assertions remain enabled for all site resources, images, fonts and API calls. tests/test_qa_analytics_stub.cjs checks that application URLs and lookalike hosts are not matched; tests/test_analytics.cjs continues to verify the production analytics logic. Real analytics-provider reachability is not covered by this isolated UI test.

Visual QA runs on relevant pull requests before merge as well as main pushes. It includes 320px, 390px and desktop checks. Do not merge before the PR checks pass.

## GitHub Pages deployment from feature branches

Run 43570879788 built successfully but its deploy failed before any steps. The workflow used to deploy on every branch, while Pages is the shared public preview. Restrict automatic Pages publication to main and guard manual dispatches from other branches. This does not disable site validation: predeploy and visual QA run on pull requests.

## Verification HTML and warm theme

Run 43578300047 failed with PAPAUTO_WARM: interior page has no head: yandex_ff7df1c7ac66fefc.html. This was already fixed before this change: the warm-theme injection requires both a document head and body. Preserve token-only verification files and the shared PUBLIC_TEXT_FILES allowlist. A successful static build must preserve the search-engine verification token bytes.

## Monitoring interpretation

Failures on older SHAs are historical when a newer run of the same workflow and branch succeeded. Compare push/PR failures separately from scheduled availability checks. The last 30 runs inspected before this change were successful; the most recent failed scheduled run was 2026-11-11T21:52:15Z. A 403 from one execution environment does not prove a general outage or Russian-network availability. Do not automatically retry deterministic defects or repeatedly deploy after an auto-deploy has started.
