/* Staging diagnostic for Netlify -> Render connection. Read-only, no lead data. */
const upstream = "https://papauto-leads.onrender.com/ready";
export default async (req: Request) => {
  const headers = { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" };
  if (req.method !== "GET") return new Response(JSON.stringify({ok:false,error:"GET_only"}),{status:405,headers});
  try {
    const response = await fetch(upstream, {
      method: "GET",
      headers: {"Accept":"application/json"},
      redirect: "error",
      signal: AbortSignal.timeout(11000),
    });
    let payload: unknown = null;
    try { payload = await response.json(); } catch {}
    const body = payload && typeof payload==="object" ? payload as Record<string,unknown> : {};
    return new Response(JSON.stringify({
      ok:response.ok && body.status==="ready" && body.database_connected===true,
      from:"netlify",
      to:"render",
      upstream_status:response.status,
      database_connected:body.database_connected===true
    }), {status:response.ok?200:502,headers});
  } catch {
    return new Response(JSON.stringify({ok:false,from:"netlify",to:"render",reason:"upstream_unreachable"}),
      {status:502,headers});
  }
};
export const config={path:"/api/upstream-check"};
