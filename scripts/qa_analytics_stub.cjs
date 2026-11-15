"use strict";
// Local UI tests must not contact live analytics or depend on their TLS/network.
// All application, photo, font and API requests retain normal browser validation.
const ANALYTICS_REQUEST = /^https:\/\/(?:mc\.yandex\.ru|www\.googletagmanager\.com)\//;
async function stubAnalytics(page) {
  await page.route(ANALYTICS_REQUEST, route => route.fulfill({
    status: 200, contentType: "application/javascript", body: "/* analytics isolated in local QA */"
  }));
}
module.exports = { ANALYTICS_REQUEST, stubAnalytics };
