"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Button, Input } from "@/components/ui";
import { adminFetch } from "@/components/admin/api";

type Claim = { id: number; issue: string; status: string; resolution_note: string };
type W = {
  id: number; invoice_number: string; customer_name: string; customer_phone: string; device: string;
  starts_on: string; ends_on: string; active: boolean; claims: Claim[];
};
const NEXT: Record<string, string[]> = {
  OPEN: ["IN_REVIEW", "APPROVED", "REJECTED"], IN_REVIEW: ["APPROVED", "REJECTED"], APPROVED: ["RESOLVED"], REJECTED: [], RESOLVED: [],
};

export function WarrantyAdmin({ apiBase }: { apiBase: string }) {
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<W[] | null>(null);
  const [issue, setIssue] = useState<Record<number, string>>({});
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    const r = await adminFetch<W[]>(apiBase, `/admin/warranty${q ? `?q=${encodeURIComponent(q)}` : ""}`);
    if (r.ok) { setRows(r.data); setError(""); } else setError(r.error);
  }, [apiBase, q]);
  useEffect(() => { load(); }, [load]);

  async function open(id: number) {
    const r = await adminFetch(apiBase, `/admin/warranty/${id}/claims`, { method: "POST", json: { issue: issue[id] ?? "" } });
    if (r.ok) { setIssue((s) => ({ ...s, [id]: "" })); load(); } else setError(r.error);
  }
  async function move(cid: number, status: string) {
    const r = await adminFetch(apiBase, `/admin/warranty/claims/${cid}`, { method: "PATCH", json: { status } });
    if (r.ok) load(); else setError(r.error);
  }

  return (
    <div className="space-y-3">
      <Input placeholder="Search invoice number or customer phone" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search warranties" />
      {error && <p role="alert" className="text-sm text-red-700">{error} <Link className="underline" href="/admin/login">Sign in</Link></p>}
      {!rows ? <p className="text-sm">Loading...</p> : !rows.length ? <p className="text-sm">No warranties yet. They are created automatically when a counter sells a device.</p> : (
        <ul className="space-y-3">
          {rows.map((w) => (
            <li key={w.id} className="space-y-2 rounded-xl border border-silver/40 bg-white p-4 text-sm">
              <div><b>{w.invoice_number}</b> · {w.device}</div>
              <div>{w.customer_name} · {w.customer_phone} · {w.starts_on} to {w.ends_on} · {w.active ? "active" : "expired"}</div>
              {w.claims.map((c) => (
                <div key={c.id} className="rounded border border-silver/40 p-2">
                  <b>Claim #{c.id}</b> [{c.status}] {c.issue}
                  <div className="mt-1 flex flex-wrap gap-2">
                    {NEXT[c.status].map((s) => <Button key={s} type="button" onClick={() => move(c.id, s)}>{s.replace("_", " ")}</Button>)}
                  </div>
                </div>
              ))}
              {w.active && (
                <div className="flex gap-2">
                  <Input placeholder="Describe the issue" value={issue[w.id] ?? ""} onChange={(e) => setIssue((s) => ({ ...s, [w.id]: e.target.value }))} aria-label="Claim issue" />
                  <Button type="button" onClick={() => open(w.id)}>Open claim</Button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
