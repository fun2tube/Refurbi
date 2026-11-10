"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui";
import { adminFetch } from "@/components/admin/api";
import { formatRupees } from "@/lib/money";

type Row = {
  id: number; number: string; status: string; total_paise: number; customer_name: string;
  email: string; phone: string; address: string; carrier: string | null; tracking_no: string | null; created_at: string;
};
type Detail = Row & {
  items: { title: string; price_paise: number; invoice_number: string | null; warranty_ends_on: string | null }[];
  timeline: { status: string; note: string; at: string }[];
};
const NEXT: Record<string, string> = { PLACED: "Mark packed", PACKED: "Ship (creates demo shipment)", SHIPPED: "Mark delivered" };

export function OrdersAdmin({ apiBase }: { apiBase: string }) {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [status, setStatus] = useState("");
  const [open, setOpen] = useState<Detail | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    const r = await adminFetch<Row[]>(apiBase, `/admin/orders${status ? `?status=${status}` : ""}`);
    if (r.ok) { setRows(r.data); setError(""); } else setError(r.error);
  }, [apiBase, status]);
  useEffect(() => { load(); }, [load]);

  async function show(id: number) {
    const r = await adminFetch<Detail>(apiBase, `/admin/orders/${id}`);
    if (r.ok) setOpen(r.data); else setError(r.error);
  }
  async function advance(id: number) {
    const r = await adminFetch<Row>(apiBase, `/admin/orders/${id}/advance`, { method: "POST" });
    if (r.ok) { await load(); await show(id); } else setError(r.error);
  }

  return (
    <div className="space-y-3 text-sm">
      {error && <p role="alert" className="text-red-700">{error} <Link className="underline" href="/admin/login">Sign in</Link></p>}
      <label className="flex items-center gap-2">Status
        <select className="rounded border border-silver/60 p-1" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All</option>
          {["PLACED", "PACKED", "SHIPPED", "DELIVERED"].map((s) => <option key={s}>{s}</option>)}
        </select>
      </label>
      {!rows ? <p>Loading...</p> : !rows.length ? <p>No online orders yet. Place one from the storefront cart (demo payment).</p> : (
        <ul className="space-y-2">
          {rows.map((o) => (
            <li key={o.id} className="rounded-xl border border-silver/40 bg-white p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span><b>{o.number}</b> · {o.status} · {formatRupees(o.total_paise)} · {o.customer_name}</span>
                <span className="flex gap-2">
                  <Button type="button" onClick={() => show(o.id)}>Details</Button>
                  {NEXT[o.status] && <Button type="button" onClick={() => advance(o.id)}>{NEXT[o.status]}</Button>}
                </span>
              </div>
              {open?.id === o.id && (
                <div className="mt-2 space-y-1 text-midnight/80">
                  <div>{o.phone} · {o.email}</div>
                  <div>{o.address}</div>
                  {o.tracking_no && <div>{o.carrier} {o.tracking_no}</div>}
                  {open.items.map((i, k) => (
                    <div key={k}>{i.title} · {formatRupees(i.price_paise)} · invoice {i.invoice_number ?? "-"} · warranty until {i.warranty_ends_on ?? "-"}</div>
                  ))}
                  <div className="text-midnight/60">{open.timeline.map((t) => `${t.status} ${new Date(t.at).toLocaleString()}`).join(" → ")}</div>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
