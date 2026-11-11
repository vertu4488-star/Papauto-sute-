/* PapAuto staging lead bridge: GitHub Pages -> Netlify -> existing Render API.
 * The Render API remains responsible for writing Neon and notifying Telegram.
 * No secrets or customer details are logged or stored by this bridge.
 * A timeout can mean the request was processed: never retry POST automatically.
 */
const ORIGINS = new Set([
  "https://vertu4488-star.github.io",
  "https://papauto.ru",
  "https://classy-genie-e78657.netlify.app",
]);
const UPSTREAM = "https://papauto-leads.onrender.com/api/leads";
const reply = (body: unknown, status: number, headers: Record<string,string>) =>
  new Response(JSON.stringify(body),{status,headers});

export default async (req: Request) => {
  const origin=req.headers.get("origin");
  const headers: Record<string,string> = {
    "Content-Type":"application/json; charset=utf-8",
    "Cache-Control":"no-store",
    "X-Content-Type-Options":"nosniff",
    "Access-Control-Allow-Methods":"POST, OPTIONS",
    "Access-Control-Allow-Headers":"content-type, accept",
    "Vary":"Origin",
  };
  if (origin && ORIGINS.has(origin)) headers["Access-Control-Allow-Origin"]=origin;
  if (!origin || !ORIGINS.has(origin))
    return reply({ok:false,reason:"origin_not_allowed"},403,headers);
  if (req.method==="OPTIONS")
    return new Response(null,{status:204,headers});
  if (req.method!=="POST")
    return reply({ok:false,reason:"method_not_allowed"},405,headers);
  if (!req.headers.get("content-type")?.toLowerCase().startsWith("application/json"))
    return reply({ok:false,reason:"json_required"},415,headers);
  let textBody:string;
  try { textBody=await req.text(); }
  catch { return reply({ok:false,reason:"body_unreadable"},400,headers); }
  if (textBody.length>7500)
    return reply({ok:false,reason:"payload_too_large"},413,headers);
  let lead: Record<string,unknown>;
  try {
    const decoded:unknown=JSON.parse(textBody);
    if (!decoded || Array.isArray(decoded) || typeof decoded!=="object") throw Error("invalid");
    lead=decoded as Record<string,unknown>;
  } catch {
    return reply({ok:false,reason:"invalid_json"},400,headers);
  }
  if (
    typeof lead.contact!=="string" || lead.contact.trim().length<3 ||
    lead.contact.length>120 ||
    typeof lead.request!=="string" || lead.request.trim().length<5 ||
    lead.request.length>4000 ||
    lead.consent!==true || lead.website!==""
  ) return reply({ok:false,reason:"invalid_lead"},422,headers);

  // Make exactly one upstream request. Never retry after network failure:
  // a lead might have been saved before the connection was interrupted.
  try {
    const response=await fetch(UPSTREAM,{
      method:"POST",
      headers:{"Content-Type":"application/json","Accept":"application/json"},
      redirect:"error",body:textBody,signal:AbortSignal.timeout(28000)
    });
    let data:unknown={};
    try { data=await response.json(); } catch {}
    // Return Render's original result/status. Browser requires ok+stored=true
    // before displaying a success dialog.
    return reply(data,response.status,headers);
  } catch {
    return reply({
      ok:false,stored:null,notified:null,
      message:"Не удалось подтвердить статус заявки. Не отправляйте повторно до проверки."
    },504,headers);
  }
};
export const config={path:"/api/leads"};
