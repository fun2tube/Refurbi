export const dynamic = "force-dynamic";

/** Liveness probe for Render + UptimeRobot keep-warm. Does not call the API (so it never blocks). */
export function GET() {
  return Response.json({ ok: true, service: "web" }, { headers: { "Cache-Control": "no-store" } });
}
