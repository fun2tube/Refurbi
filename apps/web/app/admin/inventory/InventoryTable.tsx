"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Button, Input, Select } from "@/components/ui";
import { adminFetch, qs } from "@/components/admin/api";
import { formatRupees } from "@/lib/money";

export type Row = {
  id: number; brand: string; model: string; storage_gb: number; color: string | null;
  imei_last4: string; grade: string | null; battery_health: number | null; status: string;
  location: string; price_paise: number | null; cost_paise: number; age_days: number;
};
type Page = { items: Row[]; total: number; page: number; total_pages: number };

export const STATUSES = ["PURCHASED", "IMEI_CHECKED", "QC_PENDING", "QC_PASSED", "QC_FAILED", "AVAILABLE", "RESERVED", "SOLD", "IN_TRANSIT", "RETURNED", "WARRANTY_HOLD", "REPAIR", "BLACKLISTED", "WRITTEN_OFF"];

export function InventoryTable({ apiBase }: { apiBase: string }) {
  const [f, setF] = useState({ model: "", brand: "", status: "", grade: "", min_battery: "", location_kind: "", min_age_days: "", q: "" });
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Page | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    const r = await adminFetch<Page>(apiBase, `/admin/inventory/devices${qs({ ...f, page, page_size: 25 })}`);
    setLoading(false);
    if (r.ok) { setData(r.data); setError(""); } else setError(r.error);
  }, [apiBase, f, page]);
  useEffect(() => { void load(); }, [load]);

  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => { setPage(1); setF({ ...f, [k]: e.target.value }); };

  return (
    <div className="space-y-3">
      <div className="grid gap-2 sm:grid-cols-4">
        <Input placeholder="Model" value={f.model} onChange={set("model")} aria-label="Model" />
        <Input placeholder="Brand slug (e.g. apple)" value={f.brand} onChange={set("brand")} aria-label="Brand" />
        <Input placeholder="IMEI last 4" value={f.q} onChange={set("q")} aria-label="IMEI last 4" />
        <Select value={f.status} onChange={set("status")} aria-label="Status">
          <option value="">Any status</option>
          {STATUSES.map((s) => <option key={s}>{s}</option>)}
        </Select>
        <Select value={f.grade} onChange={set("grade")} aria-label="Grade">
          <option value="">Any grade</option><option>A</option><option>B</option><option>C</option>
        </Select>
        <Input type="number" placeholder="Min battery %" value={f.min_battery} onChange={set("min_battery")} aria-label="Min battery" />
        <Select value={f.location_kind} onChange={set("location_kind")} aria-label="Location">
          <option value="">Any location</option><option value="WAREHOUSE">Warehouse</option><option value="COUNTER">Counter</option><option value="IN_TRANSIT">In transit</option>
        </Select>
        <Input type="number" placeholder="Min age (days)" value={f.min_age_days} onChange={set("min_age_days")} aria-label="Min age days" />
      </div>
      {error && <p role="alert" className="text-sm text-red-700">{error} <Link href="/admin/login" className="underline">Sign in</Link></p>}
      <div className="overflow-x-auto rounded-xl border border-silver/40 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-porcelain text-xs uppercase text-midnight/60">
            <tr>{["Device", "IMEI", "Grade", "Battery", "Status", "Location", "Age", "Cost", "Price"].map((h) => <th key={h} className="px-3 py-2">{h}</th>)}</tr>
          </thead>
          <tbody>
            {data?.items.map((d) => (
              <tr key={d.id} className="border-t border-silver/30">
                <td className="px-3 py-2"><Link className="font-medium text-brand underline" href={`/admin/inventory/${d.id}`}>{d.brand} {d.model} {d.storage_gb}GB</Link></td>
                <td className="px-3 py-2">…{d.imei_last4}</td>
                <td className="px-3 py-2">{d.grade ?? "-"}</td>
                <td className="px-3 py-2">{d.battery_health != null ? `${d.battery_health}%` : "-"}</td>
                <td className="px-3 py-2">{d.status}</td>
                <td className="px-3 py-2">{d.location}</td>
                <td className="px-3 py-2">{d.age_days}d</td>
                <td className="px-3 py-2">{formatRupees(d.cost_paise)}</td>
                <td className="px-3 py-2">{d.price_paise != null ? formatRupees(d.price_paise) : "-"}</td>
              </tr>
            ))}
            {data && data.items.length === 0 && <tr><td colSpan={9} className="px-3 py-6 text-center text-midnight/60">No devices match.</td></tr>}
            {!data && !error && <tr><td colSpan={9} className="px-3 py-6 text-center text-midnight/60">{loading ? "Loading…" : "Sign in to see inventory."}</td></tr>}
          </tbody>
        </table>
      </div>
      {data && (
        <div className="flex items-center gap-3 text-sm">
          <Button variant="ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</Button>
          <span>Page {data.page} of {Math.max(data.total_pages, 1)} · {data.total} devices</span>
          <Button variant="ghost" disabled={page >= data.total_pages} onClick={() => setPage(page + 1)}>Next</Button>
        </div>
      )}
    </div>
  );
}
