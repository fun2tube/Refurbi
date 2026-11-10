"use client";

import { useCallback, useEffect, useState } from "react";
import { Select } from "@/components/ui";
import { adminFetch } from "@/components/admin/api";
import { formatRupees } from "@/lib/money";

type Lead = {
  id: number; brand: string; model_name: string; storage_gb: number; age_band: string; screen: string; body: string;
  battery: string; powers_on: boolean; quote_low_paise: number | null; quote_high_paise: number | null;
  customer_name: string; contact: string; city: string; status: string; created_at: string;
};
const STATUSES = ["NEW", "CONTACTED", "WON", "LOST"];

export function LeadInbox({ apiBase }: { apiBase: string }) {
  const [leads, setLeads] = useState<Lead[] | null>(null);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    const r = await adminFetch<Lead[]>(apiBase, "/admin/exchange/leads");
    if (r.ok) setLeads(r.data);
    else setError(r.error);
  }, [apiBase]);
  useEffect(() => { load(); }, [load]);

  async function setStatus(id: number, status: string) {
    const r = await adminFetch<Lead>(apiBase, `/admin/exchange/leads/${id}`, { method: "PATCH", json: { status } });
    if (r.ok) setLeads((ls) => ls?.map((l) => (l.id === id ? r.data : l)) ?? null);
    else setError(r.error);
  }

  if (error) return <p role="alert" className="text-sm text-red-700">{error}</p>;
  if (!leads) return <p className="text-sm">Loading...</p>;
  if (!leads.length) return <p className="text-sm">No enquiries yet.</p>;
  return (
    <ul className="space-y-3">
      {leads.map((l) => (
        <li key={l.id} className="rounded-xl border border-silver/40 bg-white p-4 text-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <b>{l.brand} {l.model_name} · {l.storage_gb} GB</b>
            <Select value={l.status} onChange={(e) => setStatus(l.id, e.target.value)} aria-label="Status" className="w-auto">
              {STATUSES.map((s) => <option key={s}>{s}</option>)}
            </Select>
          </div>
          <div>{l.customer_name} · {l.contact}{l.city ? ` · ${l.city}` : ""}</div>
          <div className="text-midnight/70">
            Age {l.age_band}, screen {l.screen}, body {l.body}, battery {l.battery}{l.powers_on ? "" : ", does not power on"} ·{" "}
            {l.quote_low_paise !== null && l.quote_high_paise !== null ? `${formatRupees(l.quote_low_paise)} - ${formatRupees(l.quote_high_paise)}` : "needs inspection"}
          </div>
        </li>
      ))}
    </ul>
  );
}
