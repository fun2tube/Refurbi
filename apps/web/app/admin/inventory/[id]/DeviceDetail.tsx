"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Button, Card, Input, Select } from "@/components/ui";
import { adminFetch } from "@/components/admin/api";
import { formatRupees } from "@/lib/money";

type Detail = {
  id: number; brand: string; model: string; storage_gb: number; imei_last4: string; grade: string | null;
  battery_health: number | null; status: string; location: string; price_paise: number | null;
  timeline: { at: string; from: string | null; to: string; reason: string; to_location: string | null }[];
  tests: { at: string; passed: boolean; is_current: boolean; results: Record<string, string>; notes: string }[];
  photos: { id: number; url: string; kind: string }[];
};
type Template = { items: { key: string; label: string; critical: boolean }[] };
type Pricing = { purchase_paise: number; repair_paise: number; logistics_paise: number; landed_cost_paise: number; suggested_price_paise: number | null; price_paise: number | null; margin_bps: number | null };

export function DeviceDetail({ apiBase, id }: { apiBase: string; id: number }) {
  const [d, setD] = useState<Detail | null>(null);
  const [tpl, setTpl] = useState<Template | null>(null);
  const [pricing, setPricing] = useState<Pricing | null>(null);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [checks, setChecks] = useState<Record<string, string>>({});
  const [battery, setBattery] = useState("90");
  const [grade, setGrade] = useState("B");
  const [notes, setNotes] = useState("");
  const [cost, setCost] = useState({ kind: "REPAIR", rupees: "" });
  const [price, setPrice] = useState({ rupees: "", reason: "" });

  const load = useCallback(async () => {
    const r = await adminFetch<Detail>(apiBase, `/admin/inventory/devices/${id}`);
    if (!r.ok) { setError(r.error); return; }
    setError(""); setD(r.data);
    const p = await adminFetch<Pricing>(apiBase, `/admin/pricing/devices/${id}`);
    if (p.ok) setPricing(p.data);
  }, [apiBase, id]);
  useEffect(() => {
    void load();
    void adminFetch<Template>(apiBase, "/admin/qc/template").then((r) => {
      if (r.ok) { setTpl(r.data); setChecks(Object.fromEntries(r.data.items.map((i) => [i.key, "pass"]))); }
    });
  }, [apiBase, load]);

  const act = async (p: Promise<{ ok: boolean; error?: string }>, ok: string) => {
    const r = await p;
    setMsg(r.ok ? ok : `Error: ${(r as { error: string }).error}`);
    if (r.ok) await load();
  };

  if (error) return <p role="alert" className="text-sm text-red-700">{error} <Link className="underline" href="/admin/login">Sign in</Link></p>;
  if (!d) return <p className="text-sm text-midnight/60">Loading…</p>;
  const toPaise = (v: string) => Math.round(parseFloat(v || "0") * 100);

  return (
    <div className="space-y-4">
      <Link href="/admin/inventory" className="text-sm text-brand underline">← Inventory</Link>
      <h1 className="font-display text-2xl font-bold">{d.brand} {d.model} {d.storage_gb}GB</h1>
      <p className="text-sm text-midnight/70">IMEI …{d.imei_last4} · {d.status} · {d.location} · Grade {d.grade ?? "-"} · Battery {d.battery_health ?? "-"}% · Price {d.price_paise != null ? formatRupees(d.price_paise) : "-"}</p>
      {msg && <p role="status" className="rounded bg-white p-2 text-sm">{msg}</p>}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="space-y-2">
          <h2 className="font-display font-semibold">Timeline</h2>
          <ol className="space-y-1 text-sm">
            {d.timeline.map((t, i) => (
              <li key={i}>{new Date(t.at).toLocaleString()} · {t.from ?? "new"} → <strong>{t.to}</strong>{t.reason ? ` (${t.reason})` : ""}</li>
            ))}
          </ol>
        </Card>

        <Card className="space-y-2">
          <h2 className="font-display font-semibold">Pricing</h2>
          {pricing ? (
            <p className="text-sm">
              Purchase {formatRupees(pricing.purchase_paise)} + repair {formatRupees(pricing.repair_paise)} + logistics {formatRupees(pricing.logistics_paise)} = landed <strong>{formatRupees(pricing.landed_cost_paise)}</strong>.
              Suggested: {pricing.suggested_price_paise != null ? formatRupees(pricing.suggested_price_paise) : "grade needed"}.
              {pricing.margin_bps != null && ` Margin at current price: ${(pricing.margin_bps / 100).toFixed(1)}%.`}
            </p>
          ) : <p className="text-sm text-midnight/60">Pricing needs the pricing permission.</p>}
          <div className="flex flex-wrap gap-2">
            <Select value={cost.kind} onChange={(e) => setCost({ ...cost, kind: e.target.value })} className="w-32" aria-label="Cost kind"><option>REPAIR</option><option>LOGISTICS</option></Select>
            <Input type="number" placeholder="₹" value={cost.rupees} onChange={(e) => setCost({ ...cost, rupees: e.target.value })} className="w-28" aria-label="Cost rupees" />
            <Button variant="ghost" onClick={() => act(adminFetch(apiBase, `/admin/pricing/devices/${id}/costs`, { method: "POST", json: { kind: cost.kind, amount_paise: toPaise(cost.rupees) } }), "Cost added.")}>Add cost</Button>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="ghost" onClick={() => act(adminFetch(apiBase, `/admin/pricing/devices/${id}/apply-suggested`, { method: "POST" }), "Suggested price applied.")}>Apply suggested</Button>
            <Input type="number" placeholder="Override ₹" value={price.rupees} onChange={(e) => setPrice({ ...price, rupees: e.target.value })} className="w-32" aria-label="Override price" />
            <Input placeholder="Reason" value={price.reason} onChange={(e) => setPrice({ ...price, reason: e.target.value })} className="w-40" aria-label="Reason" />
            <Button variant="ghost" onClick={() => act(adminFetch(apiBase, `/admin/pricing/devices/${id}/price`, { method: "PUT", json: { price_paise: toPaise(price.rupees), reason: price.reason } }), "Price overridden.")}>Override</Button>
          </div>
        </Card>

        <Card className="space-y-2 lg:col-span-2">
          <h2 className="font-display font-semibold">QC test</h2>
          {tpl ? (
            <form className="space-y-2" onSubmit={(e) => { e.preventDefault(); void act(adminFetch(apiBase, `/admin/qc/devices/${id}/tests`, { method: "POST", json: { checklist: checks, battery_health: Number(battery), grade, notes } }), "QC saved."); }}>
              <div className="grid gap-1 sm:grid-cols-2">
                {tpl.items.map((i) => (
                  <label key={i.key} className="flex items-center justify-between gap-2 text-sm">
                    <span>{i.label}{i.critical ? " *" : ""}</span>
                    <Select className="w-24" value={checks[i.key] ?? "pass"} onChange={(e) => setChecks({ ...checks, [i.key]: e.target.value })}><option>pass</option><option>fail</option><option>na</option></Select>
                  </label>
                ))}
              </div>
              <div className="flex flex-wrap gap-2">
                <Input type="number" min={0} max={100} value={battery} onChange={(e) => setBattery(e.target.value)} className="w-28" aria-label="Battery health" />
                <Select value={grade} onChange={(e) => setGrade(e.target.value)} className="w-24" aria-label="Grade"><option>A</option><option>B</option><option>C</option></Select>
                <Input placeholder="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} className="min-w-48 flex-1" aria-label="Notes" />
                <Button type="submit">Save QC</Button>
              </div>
              <p className="text-xs text-midnight/60">* critical items must pass. Grade applies only if QC passes.</p>
            </form>
          ) : <p className="text-sm text-midnight/60">Loading template…</p>}
          <ul className="text-sm">
            {d.tests.map((t, i) => <li key={i}>{new Date(t.at).toLocaleString()} · {t.passed ? "Passed" : "Failed"}{t.is_current ? " (current)" : ""}</li>)}
          </ul>
        </Card>

        <Card className="space-y-2 lg:col-span-2">
          <h2 className="font-display font-semibold">Photos</h2>
          <div className="flex flex-wrap gap-2">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            {d.photos.map((p) => <img key={p.id} src={p.url.startsWith("/") ? `${apiBase}${p.url}` : p.url} alt={p.kind} className="h-24 w-24 rounded object-cover" />)}
          </div>
          <input type="file" accept="image/jpeg,image/png,image/webp" aria-label="Upload photo" onChange={async (e) => {
            const f = e.target.files?.[0]; if (!f) return;
            await act(adminFetch(apiBase, `/admin/qc/devices/${id}/photos`, { method: "PUT", body: f, headers: { "Content-Type": f.type } }), "Photo uploaded.");
          }} />
        </Card>
      </div>
    </div>
  );
}
