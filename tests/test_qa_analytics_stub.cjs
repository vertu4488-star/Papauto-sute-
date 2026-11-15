"use strict";
const assert = require('node:assert/strict');
const {ANALYTICS_REQUEST, stubAnalytics} = require('../scripts/qa_analytics_stub.cjs');
(async () => {
  for (const url of ['https://mc.yandex.ru/metrika/tag.js?id=114106531',
    'https://www.googletagmanager.com/gtag/js?id=G-JBPEKLFCXW']) {
    assert(ANALYTICS_REQUEST.test(url), 'Analytics must be isolated: ' + url);
  }
  for (const url of ['http://127.0.0.1:8765/gallery.js',
    'http://127.0.0.1:8765/assets/auction/approved/photo.jpg',
    'https://api.papauto.ru/api/leads', 'https://papauto.ru/',
    'https://fonts.googleapis.com/css2', 'https://mc.yandex.ru.evil.test/tag.js',
    'https://evil.test/?url=https://mc.yandex.ru/tag.js']) {
    assert(!ANALYTICS_REQUEST.test(url), 'Do not hide application or unrelated TLS errors: ' + url);
  }
  let handler;
  await stubAnalytics({route: async (pattern, callback) => {
    assert.equal(pattern, ANALYTICS_REQUEST); handler = callback;
  }});
  let response;
  await handler({fulfill: async value => {response = value;}});
  assert.equal(response.status, 200);
  assert.equal(response.contentType, 'application/javascript');
  console.log('Local QA analytics isolation passed; site/API/media requests remain unmodified');
})().catch(error => { console.error(error); process.exitCode = 1; });
