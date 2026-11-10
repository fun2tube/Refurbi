"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Button, Card, Input } from "@/components/ui";
import { adminFetch } from "@/components/admin/api";
import { formatRupees } from "@/lib/money";

type Supplier = { id: number; name: string; city: string };
type PO = { id: number; supplier_name: string; status: string; total_paise: number; lines: { id: number; variant_id: number; quantity: number; unit_cost_paise: number; received: number }[] };
type Paged<T> = { items: T[] };
type Receipt = { po_status: string; devices: { device_id: number; imei_last4: string; imei_check: string; status: string }[] };

export function ReceiveStock({ apiBase }: { apiBase: string }) {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [pos, setPos] = useState<PO[]>([]);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [sName, setSName] = useState("");
  const [imei, setImei] = useState<Record<number, string>>({});

  const load = useCallback(async () => {
    const [s, p] = await Promise.all([
      adminFetch<Paged<Supplier>>(apiBase, "/admin/procurement/suppliers?page_size=100"),
      adminFetch<Paged<PO>>(apiBase, "/admin/procurement/purchase-orders?page_size=50"),
    ]);
    if (!s.ok) { setError(s.error); return; }
    setError(""); setSuppliers(s.data.items);
    if (p.ok) setPos(p.data.items);
  }, [apiBase]);
  useEffect(() => { void load(); }, [load]);

  const run = async (p: Promise<{ ok: boolean }>, ok: string) => {
    const r = await p;
    setMsg(r.ok ? ok : `Error: ${(r as unknown as { error: string }).error}`);
    if (r.ok) await load();
    return r;
  };

  async function receive(po: PO, lineId: number) {
    const v = (imei[lineId] ?? "").trim();
    const r = await adminFetch<Receipt>(apiBase, `/admin/procurement/purchase-orders/${po.id}/receive`, { method: "POST", json: { items: [{ line_id: lineId, imei: v }] } });
    if (r.ok) {
      const x = r.data.devices[0];
      setMsg(`Received device #${x.device_id} (IMEI check ${x.imei_check}, now ${x.status}).`);
      setImei({ ...imei, [lineId]: "" });
      await load();
    } else setMsg(`Error: ${r.error}`);
  }

  if (error) return <p role="alert" className="text-sm text-red-700">{error} <Link className="underline" href="/admin/login">Sign in</Link></p>;
  return (
    <div className="space-y-4">
      {msg && <p role="status" className="rounded bg-white p-2 text-sm">{msg}</p>}
      <Card className="space-y-2">
        <h2 className="font-display font-semibold">Suppliers</h2>
        <ul className="text-sm">{suppliers.map((s) => <li key={s.id}>{s.name} {s.city && `· ${s.city}`}</li>)}</ul>
        <div className="flex gap-2">
          <Input placeholder="New supplier name" value={sName} onChange={(e) => setSName(e.target.value)} aria-label="Supplier name" />
          <Button variant="ghost" onClick={async () => { const r = await run(adminFetch(apiBase, "/admin/procurement/suppliers", { method: "POST", json: { name: sName } }), "Supplier added."); if (r.ok) setSName(""); }}>Add</Button>
        </div>
      </Card>
      <h2 className="font-display text-lg font-semibold">Purchase orders</h2>
      {pos.length === 0 && <p className="text-sm text-midnight/60">No purchase orders yet (create via the API for now).</p>}
      {pos.map((po) => (
        <Card key={po.id} className="space-y-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="font-medium">PO #{po.id} · {po.supplier_name} · {po.status} · {formatRupees(po.total_paise)}</div>
            {po.status === "DRAFT" && <Button variant="ghost" onClick={() => run(adminFetch(apiBase, `/admin/procurement/purchase-orders/${po.id}/order`, { method: "POST" }), "PO marked ordered.")}>Mark ordered</Button>}
          </div>
          {po.lines.map((l) => (
            <div key={l.id} className="flex flex-wrap items-center gap-2 text-sm">
              <span>Variant #{l.variant_id}: {l.received}/{l.quantity} received @ {formatRupees(l.unit_cost_paise)}</span>
              {["ORDERED", "PARTIALLY_RECEIVED"].includes(po.status) && l.received < l.quantity && (
                <>
                  <Input className="w-48" placeholder="IMEI (15 digits)" value={imei[l.id] ?? ""} onChange={(e) => setImei({ ...imei, [l.id]: e.target.value })} aria-label={`IMEI for line ${l.id}`} />
                  <Button onClick={() => receive(po, l.id)}>Receive</Button>
                </>
              )}
            </div>
          ))}
        </Card>
      ))}
    </div>
  );
}
