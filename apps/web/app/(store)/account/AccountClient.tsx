"use client";
import { useState } from "react";
import Link from "next/link";
import { Button, Input } from "@/components/ui";
import { formatRupees } from "@/lib/money";

type Order = { number: string; token: string; status: string; total_paise: number; placed_at: string; items: { title: string; invoice_number: string | null; warranty_ends_on: string | null; warranty_active: boolean | null }[] };

export function AccountClient({ apiBase }: { apiBase: string }) {
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState<"email" | "otp" | "list">("email");
  const [demo, setDemo] = useState("");
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const post = (p: string, b: unknown) =>
    fetch(`${apiBase}${p}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) });

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setError("");
    try {
      if (step === "email") {
        const r = await post("/public/reservations/otp", { email });
        if (!r.ok) return setError(r.status === 429 ? "Too many attempts - please wait a few minutes." : "Please check your email address.");
        setDemo((await r.json()).demo_code ?? ""); setStep("otp");
      } else {
        const r = await post("/public/account/orders", { email, otp });
        if (!r.ok) return setError(r.status === 400 ? "That code is wrong or expired." : "Something went wrong - please retry.");
        setOrders(await r.json()); setStep("list");
      }
    } catch { setError("Could not reach the server (it may be waking up) - please retry."); } finally { setBusy(false); }
  }

  if (step === "list")
    return orders.length ? (
      <ul className="mt-6 space-y-3">
        {orders.map((o) => (
          <li key={o.token} className="rounded-xl border border-silver/40 bg-white p-3 text-sm">
            <Link className="font-semibold text-brand underline" href={`/orders/${o.token}`}>{o.number}</Link>
            {" "}· {o.status} · {formatRupees(o.total_paise)}
            {o.items.map((i, k) => (
              <div key={k} className="text-midnight/70">
                {i.title}
                {i.invoice_number && <> · <a className="text-brand underline" href={`${apiBase}/public/orders/${o.token}/invoice.pdf?number=${encodeURIComponent(i.invoice_number)}`}>Invoice {i.invoice_number}</a></>}
                {i.warranty_ends_on && <> · Warranty {i.warranty_active ? "until" : "ended"} {i.warranty_ends_on}</>}
              </div>
            ))}
          </li>
        ))}
      </ul>
    ) : <p className="mt-6 text-sm">No orders found for this email yet. <Link className="text-brand underline" href="/refurbished-mobiles">Browse phones</Link></p>;

  return (
    <form onSubmit={submit} className="mt-6 grid max-w-sm gap-3">
      <Input aria-label="Email" type="email" placeholder="Email" required value={email} onChange={(e) => setEmail(e.target.value)} disabled={step === "otp"} />
      {step === "otp" && <Input aria-label="6-digit code" inputMode="numeric" placeholder="6-digit code" required minLength={4} maxLength={8} value={otp} onChange={(e) => setOtp(e.target.value)} />}
      {demo && step === "otp" && <p className="text-xs text-midnight/60">Demo mode (no email service connected): your code is {demo}</p>}
      <Button type="submit" disabled={busy}>{busy ? "Please wait..." : step === "email" ? "Send code" : "Show my orders"}</Button>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
    </form>
  );
}
