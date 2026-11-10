"use client";

import { useState } from "react";
import { Button, Input } from "@/components/ui";

type Res = { invoice_number: string; device: string; starts_on: string; ends_on: string; months: number; active: boolean };

export function WarrantyLookup({ apiBase }: { apiBase: string }) {
  const [phone, setPhone] = useState("");
  const [invoice, setInvoice] = useState("");
  const [res, setRes] = useState<Res | null>(null);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(""); setRes(null);
    try {
      const r = await fetch(`${apiBase}/public/warranty/lookup`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone, invoice_number: invoice }),
      });
      if (r.ok) setRes(await r.json());
      else setError(r.status === 404 ? "No warranty found for these details." : r.status === 429 ? "Too many tries. Please wait a few minutes." : "Something went wrong. Please try again.");
    } catch { setError("Could not reach the server. Please try again in a minute."); }
  }
  return (
    <form onSubmit={submit} className="space-y-3 text-sm">
      <label className="block">Mobile number<Input value={phone} onChange={(e) => setPhone(e.target.value)} inputMode="numeric" required /></label>
      <label className="block">Invoice number<Input value={invoice} onChange={(e) => setInvoice(e.target.value)} required /></label>
      <Button type="submit">Check warranty</Button>
      {error && <p role="alert" className="text-red-700">{error}</p>}
      {res && (
        <p className="rounded-lg border border-silver/40 bg-white p-3">
          <b>{res.device}</b><br />Invoice {res.invoice_number}<br />
          {res.starts_on} to {res.ends_on} ({res.months} months) - {res.active ? "in warranty" : "warranty period ended"}
        </p>
      )}
    </form>
  );
}
