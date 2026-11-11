/* PapAuto read-only network/POST connectivity test for Netlify.
 * Does not store data, notify Telegram, or accept real contact details.
 * GET /api/network-check, POST /api/network-check (dummy payload only).
 */
const allowedOrigins = new Set([
  "https://vertu4488-star.github.io",
  "https://papauto.ru",
]);
const headers = (origin: string | null) => {
  const h: Record<string, string> = {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "content-type",
    "Vary": "Origin",
  };
  if (origin && allowedOrigins.has(origin)) {
    h["Access-Control-Allow-Origin"] = origin;
  }
  return h;
};
const json = (body: unknown, status: number, h: Record<string, string>) =>
  new Response(JSON.stringify(body), { status, headers: h });

export default async (req: Request) => {
  const origin = req.headers.get("origin");
  const h = headers(origin);
  if (origin && !allowedOrigins.has(origin)) {
    return json({ ok: false, reason: "origin_not_allowed" }, 403, h);
  }
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: h });
  }
  if (req.method === "GET") {
    return json({
      ok: true,
      service: "papauto-netlify-api-probe",
      method: "GET",
      stored: false,
      notified: false,
      timestamp: new Date().toISOString(),
    }, 200, h);
  }
  if (req.method !== "POST") {
    return json({ ok: false, reason: "method_not_allowed" }, 405, h);
  }
  // Consume only a very small, exact test request; never accept client records.
  if (!req.headers.get("content-type")?.startsWith("application/json")) {
    return json({ ok: false, reason: "json_required" }, 415, h);
  }
  let raw: string;
  try {
    raw = await req.text();
  } catch {
    return json({ ok: false, reason: "invalid_body" }, 400, h);
  }
  if (raw.length > 256) return json({ ok: false, reason: "too_large" }, 413, h);
  let payload: unknown;
  try { payload = JSON.parse(raw); } catch {
    return json({ ok: false, reason: "invalid_json" }, 400, h);
  }
  const valid = payload !== null && typeof payload === "object" &&
    Object.keys(payload).sort().join(",") === "kind,nonce" &&
    (payload as Record<string, unknown>).kind === "network-check" &&
    (payload as Record<string, unknown>).nonce === "papauto-20261111";
  if (!valid) return json({ ok: false, reason: "test_payload_only" }, 422, h);
  return json({
    ok: true,
    received: true,
    stored: false,
    notified: false,
    service: "papauto-netlify-api-probe",
    method: "POST",
  }, 200, h);
};

export const config = { path: "/api/network-check" };
