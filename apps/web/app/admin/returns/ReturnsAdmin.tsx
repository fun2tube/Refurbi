"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui";
import { adminFetch } from "@/components/admin/api";
import { formatRupees } from "@/lib/money";

type Row = {
  id: number; order_number: string; item: string; invoice_number: string | null; price_paise: number;
  reason: string; status: string; refund_paise: number; refund_ref: string | null;
};
// status -> [label, action path]; REQUESTED has approve and reject
const STEP: Record<string, [string, string]> = { APPROVED: ["Mark device received", "receive"], RECEIVED: ["Refund in full", "refund"] };

export function ReturnsAdmin({ apiBase }: { apiBase: string }) {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    const r = await adminFetch<Row[]>(apiBase, "/admin/returns");
    if (r.ok) { setRows(r.data); setError(""); } else setError(r.error);
  }, [apiBase]);
  useEffect(() => { load(); }, [load]);
  async function act(id: number, path: string) {
    const r = await adminFetch<Row>(apiBase, `/admin/returns/${id}/${path}`, { method: "POST", json: {} });
    if (r.ok) load(); else setError(r.error);
  }
  return (
    <div className="space-y-3 text-sm">
      {error && <p role="alert" className="text-red-700">{error} <Link className="underline" href="/admin/login">Sign in</Link></p>}
      {!rows ? <p>Loading...</p> : !rows.length ? <p>No return requests yet.</p> : (
        <ul className="space-y-2">
          {rows.map((r) => (
            <li key={r.id} className="rounded-xl border border-silver/40 bg-white p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span><b>{r.order_number}</b> · {r.item} · {formatRupees(r.price_paise)} · <b>{r.status}</b>{r.status === "REFUNDED" && ` ${formatRupees(r.refund_paise)} (${r.refund_ref})`}</span>
                <span className="flex gap-2">
                  {r.status === "REQUESTED" && <>
                    <Button type="button" onClick={() => act(r.id, "approve")}>Approve</Button>
                    <Button type="button" onClick={() => act(r.id, "reject")}>Reject</Button>
                  </>}
                  {STEP[r.status] && <Button type="button" onClick={() => act(r.id, STEP[r.status][1])}>{STEP[r.status][0]}</Button>}
                </span>
              </div>
              <div className="text-midnight/70">Reason: {r.reason}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
