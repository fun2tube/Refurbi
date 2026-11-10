"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui";
import { adminFetch } from "@/components/admin/api";
import { formatRupees } from "@/lib/money";

type Row = { counter_id: number; counter: string; unsettled_units: number; unsettled_commission_paise: number };
type Statement = {
  unsettled: { units: number; sales_total_paise: number; commission_paise: number; net_due_to_refurbi_paise: number };
  entries: { invoice_number: string; sale_price_paise: number; commission_paise: number; status: string }[];
};

export function Commissions({ apiBase }: { apiBase: string }) {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [open, setOpen] = useState<number | null>(null);
  const [st, setSt] = useState<Statement | null>(null);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");

  const load = useCallback(async () => {
    const r = await adminFetch<Row[]>(apiBase, "/admin/commissions/summary");
    if (r.ok) { setRows(r.data); setError(""); } else setError(r.error);
  }, [apiBase]);
  useEffect(() => { load(); }, [load]);

  async function show(id: number) {
    setOpen(id); setMsg("");
    const r = await adminFetch<Statement>(apiBase, `/admin/commissions/counters/${id}/statement`);
    if (r.ok) setSt(r.data); else setError(r.error);
  }
  async function settle(id: number) {
    const r = await adminFetch<{ commission_paise: number }>(apiBase, "/admin/commissions/settlements", { method: "POST", json: { counter_id: id } });
    if (r.ok) { setMsg(`Settled ${formatRupees(r.data.commission_paise)}.`); load(); show(id); } else setError(r.error);
  }

  return (
    <div className="space-y-3 text-sm">
      {error && <p role="alert" className="text-red-700">{error} <Link className="underline" href="/admin/login">Sign in</Link></p>}
      {msg && <p className="text-green-800">{msg}</p>}
      {!rows ? <p>Loading...</p> : !rows.length ? <p>No unsettled commission. Sell a device in /partner first (needs a commission rule on the counter).</p> : (
        <ul className="space-y-2">
          {rows.map((r) => (
            <li key={r.counter_id} className="rounded-xl border border-silver/40 bg-white p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span><b>{r.counter}</b> · {r.unsettled_units} units · {formatRupees(r.unsettled_commission_paise)}</span>
                <span className="flex gap-2">
                  <Button type="button" onClick={() => show(r.counter_id)}>Statement</Button>
                  <Button type="button" onClick={() => settle(r.counter_id)}>Mark settled</Button>
                </span>
              </div>
              {open === r.counter_id && st && (
                <div className="mt-2 space-y-1">
                  <div>Sales {formatRupees(st.unsettled.sales_total_paise)} − commission {formatRupees(st.unsettled.commission_paise)} = due to Refurbi {formatRupees(st.unsettled.net_due_to_refurbi_paise)}</div>
                  {st.entries.map((e) => <div key={e.invoice_number} className="text-midnight/70">{e.invoice_number} · {formatRupees(e.sale_price_paise)} · {formatRupees(e.commission_paise)} · {e.status}</div>)}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
