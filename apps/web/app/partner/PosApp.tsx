"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Button, Input, Select } from "@/components/ui";
import { adminFetch, getToken } from "@/components/admin/api";
import { formatRupees } from "@/lib/money";

type Me = { email: string; roles: { code: string; counter_id: number | null }[] };
type Item = {
  device_id: number; brand: string; model: string; storage_gb: number; color: string | null;
  grade: string | null; battery_health: number | null; imei_last4: string; price_paise: number | null;
};
type SaleOut = {
  invoice_number: string; invoice_pdf_url: string; total_paise: number; payment_mode: string;
  whatsapp_url: string; upi_uri?: string;
};

export function PosApp({ apiBase }: { apiBase: string }) {
  const [counterId, setCounterId] = useState<number | null>(null);
  const [counterInput, setCounterInput] = useState("1");
  const [needsPick, setNeedsPick] = useState(false);
  const [q, setQ] = useState("");
  const [items, setItems] = useState<Item[] | null>(null);
  const [sel, setSel] = useState<Item | null>(null);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [mode, setMode] = useState("CASH");
  const [ref, setRef] = useState("");
  const [done, setDone] = useState<SaleOut | null>(null);
  const [error, setError] = useState("");
  const [signedOut, setSignedOut] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!getToken()) { setSignedOut(true); return; }
    adminFetch<Me>(apiBase, "/auth/me").then((r) => {
      if (!r.ok) { setSignedOut(true); setError(r.error); return; }
      const own = r.data.roles.find((x) => x.counter_id !== null);
      if (own) setCounterId(own.counter_id);
      else setNeedsPick(true); // global admin: choose a counter id
    });
  }, [apiBase]);

  const load = useCallback(async () => {
    if (counterId === null) return;
    const r = await adminFetch<Item[]>(apiBase, `/pos/counters/${counterId}/stock${q ? `?q=${encodeURIComponent(q)}` : ""}`);
    if (r.ok) { setItems(r.data); setError(""); } else setError(r.error);
  }, [apiBase, counterId, q]);
  useEffect(() => { load(); }, [load]);

  async function sell(e: React.FormEvent) {
    e.preventDefault();
    if (!sel || counterId === null) return;
    setBusy(true);
    const r = await adminFetch<SaleOut>(apiBase, `/pos/counters/${counterId}/sales`, {
      method: "POST",
      json: { device_id: sel.device_id, customer_name: name, customer_phone: phone, payment_mode: mode, payment_ref: ref },
    });
    setBusy(false);
    if (r.ok) { setDone(r.data); setSel(null); setName(""); setPhone(""); setRef(""); load(); } else setError(r.error);
  }

  async function openPdf(url: string) {
    const token = getToken();
    const res = await fetch(`${apiBase}${url}`, { headers: { Authorization: `Bearer ${token}` } });
    if (res.ok) window.open(URL.createObjectURL(await res.blob()), "_blank");
    else setError("Could not open the invoice PDF.");
  }

  if (signedOut) return <p className="text-sm">{error || "Please sign in first."} <Link className="underline" href="/admin/login">Sign in</Link></p>;
  if (needsPick && counterId === null) {
    return (
      <form className="max-w-xs space-y-2 text-sm" onSubmit={(e) => { e.preventDefault(); setCounterId(Number(counterInput)); }}>
        <label className="block">Counter id (admin view)<Input value={counterInput} onChange={(e) => setCounterInput(e.target.value)} inputMode="numeric" /></label>
        <Button type="submit">Open counter POS</Button>
      </form>
    );
  }
  if (done) {
    return (
      <div className="max-w-md space-y-3 rounded-xl border border-silver/40 bg-white p-4 text-sm">
        <h2 className="font-display text-lg font-bold">Sale recorded</h2>
        <p>Invoice <b>{done.invoice_number}</b> · {formatRupees(done.total_paise)} · {done.payment_mode}</p>
        {done.upi_uri && (
          <p>Customer pays by UPI: <a className="break-all text-brand underline" href={done.upi_uri}>open UPI app link</a> (show this link as a QR from any UPI app, then confirm payment received).</p>
        )}
        <div className="flex flex-wrap gap-2">
          <Button type="button" onClick={() => openPdf(done.invoice_pdf_url)}>View invoice PDF</Button>
          <a className="rounded-lg border border-brand px-3 py-2 text-brand" href={done.whatsapp_url} target="_blank" rel="noreferrer">Share on WhatsApp</a>
          <Button type="button" onClick={() => setDone(null)}>New sale</Button>
        </div>
      </div>
    );
  }
  return (
    <div className="space-y-4">
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      {sel ? (
        <form onSubmit={sell} className="max-w-md space-y-3 rounded-xl border border-silver/40 bg-white p-4 text-sm">
          <div><b>{sel.brand} {sel.model}</b> · {sel.storage_gb} GB · Grade {sel.grade ?? "-"} · IMEI ending {sel.imei_last4}</div>
          <div className="text-lg font-bold">{sel.price_paise !== null ? formatRupees(sel.price_paise) : "No price"}</div>
          <label className="block">Customer name<Input value={name} onChange={(e) => setName(e.target.value)} required /></label>
          <label className="block">Customer mobile (10 digits)<Input value={phone} onChange={(e) => setPhone(e.target.value)} inputMode="numeric" pattern="[6-9][0-9]{9}" required /></label>
          <label className="block">Payment mode
            <Select value={mode} onChange={(e) => setMode(e.target.value)}>
              <option value="CASH">Cash</option><option value="UPI">UPI (QR)</option><option value="CARD">Card (recorded manually)</option>
            </Select>
          </label>
          {mode !== "CASH" && <label className="block">{mode === "UPI" ? "UPI transaction id" : "Card slip / last 4 digits"}<Input value={ref} onChange={(e) => setRef(e.target.value)} /></label>}
          <div className="flex gap-2">
            <Button type="submit" disabled={busy}>{busy ? "Saving..." : "Confirm sale and issue invoice"}</Button>
            <Button type="button" onClick={() => setSel(null)}>Back</Button>
          </div>
        </form>
      ) : (
        <>
          <Input placeholder="Search model, brand or IMEI last 4" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search stock" />
          {!items ? <p className="text-sm">Loading...</p> : !items.length ? <p className="text-sm">No available stock at this counter.</p> : (
            <ul className="space-y-2">
              {items.map((i) => (
                <li key={i.device_id}>
                  <button type="button" onClick={() => setSel(i)} className="w-full rounded-xl border border-silver/40 bg-white p-3 text-left text-sm">
                    <b>{i.brand} {i.model}</b> · {i.storage_gb} GB · Grade {i.grade ?? "-"} · …{i.imei_last4}
                    <span className="float-right font-semibold">{i.price_paise !== null ? formatRupees(i.price_paise) : "-"}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}
