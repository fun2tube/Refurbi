"use client";

import { useState } from "react";
import { Button, Input, Select } from "@/components/ui";
import { formatRupees } from "@/lib/money";

type Quote = { low_paise: number | null; high_paise: number | null; needs_inspection: boolean; disclaimer: string };

const OPTS = {
  age_band: [["under_1", "Under 1 year"], ["1_2", "1-2 years"], ["2_3", "2-3 years"], ["3_4", "3-4 years"], ["over_4", "Over 4 years"]],
  screen: [["perfect", "No marks"], ["scratches", "Light scratches"], ["cracked", "Cracked"]],
  body: [["perfect", "No marks"], ["dents", "Dents / scuffs"], ["damaged", "Bent or damaged"]],
  battery: [["good", "Lasts a full day"], ["fair", "Needs a top-up"], ["poor", "Drains fast"]],
} as const;

export function ExchangeForm({ apiBase }: { apiBase: string }) {
  const [f, setF] = useState({
    brand: "", model_name: "", storage_gb: "128", age_band: "1_2", screen: "perfect", body: "perfect", battery: "good",
    has_accessories: true, powers_on: true, customer_name: "", contact: "", city: "",
  });
  const [quote, setQuote] = useState<Quote | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k: string, v: string | boolean) => setF((p) => ({ ...p, [k]: v }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${apiBase}/public/exchange/leads`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...f, storage_gb: Number(f.storage_gb) }),
      });
      if (res.status === 429) setError("Too many requests - please try again in a few minutes.");
      else if (!res.ok) setError("Please check the form and try again.");
      else setQuote(await res.json());
    } catch {
      setError("Could not reach the server (it may be waking up) - please retry in a minute.");
    }
    setBusy(false);
  }

  if (quote)
    return (
      <div className="mt-6 max-w-xl rounded-2xl border border-silver/40 bg-white p-6" role="status">
        {quote.needs_inspection || quote.low_paise === null || quote.high_paise === null ? (
          <p className="font-display text-xl font-semibold">We need to inspect it first</p>
        ) : (
          <>
            <p className="text-sm text-midnight/70">Indicative range (demo estimate)</p>
            <p className="font-display text-3xl font-bold">{formatRupees(quote.low_paise)} - {formatRupees(quote.high_paise)}</p>
          </>
        )}
        <p className="mt-3 text-sm text-midnight/70">{quote.disclaimer}</p>
        <p className="mt-3 text-sm">Thanks - we have saved your enquiry and will contact you to arrange the inspection.</p>
      </div>
    );

  const sel = (k: keyof typeof OPTS, label: string) => (
    <label className="block text-sm">
      {label}
      <Select value={f[k]} onChange={(e) => set(k, e.target.value)} className="mt-1">
        {OPTS[k].map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </Select>
    </label>
  );

  return (
    <form onSubmit={submit} className="mt-6 grid max-w-xl gap-4">
      <div className="grid grid-cols-2 gap-3">
        <label className="block text-sm">Brand<Input required maxLength={60} value={f.brand} onChange={(e) => set("brand", e.target.value)} className="mt-1" /></label>
        <label className="block text-sm">Model<Input required maxLength={120} value={f.model_name} onChange={(e) => set("model_name", e.target.value)} className="mt-1" /></label>
      </div>
      <label className="block text-sm">Storage
        <Select value={f.storage_gb} onChange={(e) => set("storage_gb", e.target.value)} className="mt-1">
          {[64, 128, 256, 512].map((s) => <option key={s} value={s}>{s} GB</option>)}
        </Select>
      </label>
      {sel("age_band", "Age of the phone")}
      {sel("screen", "Screen condition")}
      {sel("body", "Body condition")}
      {sel("battery", "Battery")}
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.has_accessories} onChange={(e) => set("has_accessories", e.target.checked)} /> I have the box / charger</label>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.powers_on} onChange={(e) => set("powers_on", e.target.checked)} /> The phone switches on</label>
      <div className="grid grid-cols-2 gap-3">
        <label className="block text-sm">Your name<Input required maxLength={120} value={f.customer_name} onChange={(e) => set("customer_name", e.target.value)} className="mt-1" /></label>
        <label className="block text-sm">Phone or email<Input required minLength={5} maxLength={160} value={f.contact} onChange={(e) => set("contact", e.target.value)} className="mt-1" /></label>
      </div>
      <label className="block text-sm">City (optional)<Input maxLength={80} value={f.city} onChange={(e) => set("city", e.target.value)} className="mt-1" /></label>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <Button type="submit" disabled={busy}>{busy ? "Checking..." : "Get my estimate"}</Button>
      <p className="text-xs text-midnight/60">We use your contact details only to follow up on this enquiry.</p>
    </form>
  );
}
