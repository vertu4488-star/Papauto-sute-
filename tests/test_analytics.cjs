"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

// Isolated browser simulation: does not send analytics or contact customers.
const script = fs.readFileSync(path.join(__dirname, "../metrika.js"), "utf8");
const METRIKA_ID = 114106531;
const GA_ID = "G-JBPEKLFCXW";

function boot(homepage = false) {
  const documentEvents = {};
  const windowEvents = {};
  const loadedScripts = [];
  const manualGaCalls = [];
  const parent = { insertBefore: (node) => loadedScripts.push(node) };
  const document = {
    scripts: loadedScripts,
    createElement: () => ({ async: false, src: "" }),
    getElementsByTagName: () => [{ parentNode: parent }],
    head: { appendChild: (node) => loadedScripts.push(node) },
    addEventListener: (type, handler) => { documentEvents[type] = handler; },
  };
  const window = {
    addEventListener: (type, handler) => { windowEvents[type] = handler; },
  };
  if (homepage) {
    // The real homepage supplies gtag and its own GA4 contact listeners.
    window.gtag = (...args) => manualGaCalls.push(args);
  }
  // A browser exposes window properties (including ym) as global identifiers.
  Object.assign(window, { document, window, Date });
  vm.runInNewContext(script, window, { timeout: 2000 });

  const yandexCalls = () => Array.from(window.ym.a || [], (args) => Array.from(args));
  const googleCalls = () => homepage
    ? manualGaCalls
    : Array.from(window.dataLayer || [], (args) => Array.from(args));
  const events = (name) => googleCalls().filter((args) => args[0] === "event" && args[1] === name);
  const goals = (name) => yandexCalls().filter((args) => args[0] === METRIKA_ID && args[1] === "reachGoal" && args[2] === name);
  const click = (href) => {
    assert.equal(typeof documentEvents.click, "function");
    documentEvents.click({ target: { closest: () => ({ getAttribute: () => href }) } });
  };
  return { window, windowEvents, loadedScripts, googleCalls, events, goals, click };
}

const seo = boot(false);
assert.equal(seo.loadedScripts.filter((s) => s.src.includes("mc.yandex.ru/metrika/tag.js")).length, 1, "One Yandex tag expected");
assert.equal(seo.loadedScripts.filter((s) => s.src.includes("googletagmanager.com/gtag/js")).length, 1, "GA4 must load exactly once on SEO pages");
assert.equal(seo.googleCalls().filter((args) => args[0] === "config" && args[1] === GA_ID).length, 1, "One GA4 page view configuration");

seo.click("tel:+79139159641");
assert.equal(seo.goals("phone_click").length, 1, "Yandex phone goal");
assert.equal(seo.events("contact_phone_click").length, 1, "GA4 phone event");

seo.click("https://t.me/New_Iphone_Service");
assert.equal(seo.goals("telegram_click").length, 1, "Yandex Telegram goal");
assert.equal(seo.events("contact_telegram_click").length, 1, "GA4 Telegram event");

seo.click("https://telegram.me/example");
assert.equal(seo.goals("telegram_click").length, 2, "Telegram alternative domain");
seo.click("https://not-t.me/evil");
assert.equal(seo.goals("telegram_click").length, 2, "Unrelated domain cannot count as Telegram");

const homepage = boot(true);
assert.equal(homepage.loadedScripts.filter((s) => s.src.includes("googletagmanager.com/gtag/js")).length, 0, "Do not initialize GA4 twice on home");
homepage.click("tel:+79139159641");
homepage.click("https://t.me/New_Iphone_Service");
assert.equal(homepage.goals("phone_click").length, 1, "Yandex phone homepage goal");
assert.equal(homepage.goals("telegram_click").length, 1, "Yandex Telegram homepage goal");
assert.equal(homepage.events("contact_phone_click").length, 0, "Shared script must leave homepage GA events to homepage handler");
assert.equal(homepage.events("contact_telegram_click").length, 0, "No double-counting GA Telegram on homepage");

assert.equal(typeof seo.windowEvents["papauto:lead-submitted"], "function", "Server-confirmed lead handler must exist");
seo.windowEvents["papauto:lead-submitted"]({ detail: { phone: "+79000000000", name: "Private Test" } });
assert.equal(seo.goals("generate_lead").length, 1, "Yandex lead goal");
assert.equal(seo.events("generate_lead").length, 1, "GA4 lead event");
const leadPayload = JSON.stringify(seo.events("generate_lead")[0]);
assert.ok(!leadPayload.includes("+79000000000") && !leadPayload.includes("Private Test"), "Never leak lead PII to analytics");

process.stdout.write("PASS analytics: Yandex goals, GA4 events, duplicate protection, server-confirmed leads\n");
