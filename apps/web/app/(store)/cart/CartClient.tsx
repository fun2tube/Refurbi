"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Button, Input } from "@/components/ui";
import { readCart, removeFromCart, writeCart } from "@/lib/cart";
import { formatRupees } from "@/lib/money";

type Line = { unit_id: number; available: boolean; price_paise: number | null };
type Hold = {
  token: string; status: string; total_paise: number; expires_at: string; seconds_left: number;
  hold_minutes: number; items: { unit_id: number; price_paise: number }[];
  delivery: { min_days: number; max_days: number } | null;
};

export function CartClient({ apiBase }: { apiBase: string }) {
  const [ids, setIds] = useState<number[] | null>(null);
  const [lines, setLines] = useState<Line[]>([]);
  const [step, setStep] = useState<"cart" | "otp" | "held">("cart");
  const [f, setF] = useState({ name: "", email: "", phone: "", address_line: "", city: "", pincode: "" });
  const [otp, setOtp] = useState("");
  const [demo, setDemo] = useState("");
  const [hold, setHold] = useState<Hold | null>(null);
  const [left, setLeft] = useState(0);
  const [est, setEst] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const c = readCart();
    setIds(c);
    if (!c.length || !apiBase) return setLines([]);
    try {
      const r = await fetch(`${apiBase}/public/cart?ids=${c.join(",")}`);
      if (r.ok) setLines(await r.json());
    } catch {
      setError("Could not reach the server (it may be waking up) - please refresh in a minute.");
    }
  }, [apiBase]);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    if (step !== "held" || !hold) return;
    const t = setInterval(() => setLeft((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(t);
  }, [step, hold]);

  const ok = lines.filter((l) => l.available);
  const total = ok.reduce((s, l) => s + (l.price_paise ?? 0), 0);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement>) => setF({ ...f, [k]: e.target.value });
  const post = (p: string, b: unknown) =>
    fetch(`${apiBase}${p}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) });
  const fail = (s: number) =>
    setError(
      s === 429 ? "Too many attempts - please wait a few minutes."
      : s === 404 ? "A phone in your cart was just taken. Please refresh your cart."
      : s === 400 ? "That code is wrong or expired."
      : "Please check your details and try again.",
    );

  async function pin(p: string) {
    setEst("");
    if (!/^[1-9][0-9]{5}$/.test(p)) return;
    try {
      const r = await fetch(`${apiBase}/public/delivery-estimate?pincode=${p}`);
      if (r.ok) { const j = await r.json(); setEst(`Estimated delivery: ${j.min_days}-${j.max_days} days (indicative)`); }
    } catch { /* estimate is optional */ }
  }

  async function sendCode(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setError("");
    try {
      const r = await post("/public/reservations/otp", { email: f.email });
      if (!r.ok) return fail(r.status);
      setDemo((await r.json()).demo_code ?? ""); setStep("otp");
    } catch { setError("Could not reach the server - please retry."); } finally { setBusy(false); }
  }

  async function confirm(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setError("");
    try {
      const r = await post("/public/checkout", { ...f, unit_ids: ok.map((l) => l.unit_id), otp });
      if (!r.ok) { if (r.status === 404) void load(); return fail(r.status); }
      const h: Hold = await r.json();
      setHold(h); setLeft(h.seconds_left); setStep("held"); writeCart([]);
    } catch { setError("Could not reach the server - please retry."); } finally { setBusy(false); }
  }

  async function cancel() {
    if (!hold) return;
    await fetch(`${apiBase}/public/checkout/${hold.token}/cancel`, { method: "POST" }).catch(() => undefined);
    setHold(null); setStep("cart"); void load();
  }

  if (step === "held" && hold) {
    const mm = String(Math.floor(left / 60)).padStart(2, "0"), ss = String(left % 60).padStart(2, "0");
    return (
      <div role="status" className="mt-6 max-w-lg rounded-2xl bg-porcelain p-5">
        {left > 0 ? (
          <>
            <p className="font-display text-lg font-semibold">Your phones are held for {mm}:{ss}</p>
            <p className="mt-1 text-sm text-midnight/70">Total {formatRupees(hold.total_paise)}. Online payment is not switched on yet in this preview; nothing has been charged.</p>
            {hold.delivery && <p className="mt-1 text-sm text-midnight/70">Estimated delivery {hold.delivery.min_days}-{hold.delivery.max_days} days (indicative).</p>}
            <Button type="button" className="mt-4" onClick={cancel}>Release hold</Button>
          </>
        ) : (
          <p className="font-display font-semibold">The hold has expired and the phones are back in stock. <Link className="text-brand underline" href="/refurbished-mobiles">Browse phones</Link></p>
        )}
      </div>
    );
  }

  if (ids === null) return <p className="mt-6 text-sm text-midnight/70">Loading your cart...</p>;
  if (!ids.length)
    return (
      <p className="mt-6 text-sm">
        Your cart is empty. <Link className="text-brand underline" href="/refurbished-mobiles">Browse phones</Link>
      </p>
    );

  return (
    <div className="mt-6 grid gap-8 md:grid-cols-2">
      <ul className="space-y-3">
        {lines.map((l) => (
          <li key={l.unit_id} className="flex items-center justify-between rounded-xl border border-silver/40 bg-white p-3 text-sm">
            <span>
              Phone #{l.unit_id}{" "}
              {l.available ? <b className="ml-2">{formatRupees(l.price_paise ?? 0)}</b> : <em className="ml-2 text-red-700">no longer available</em>}
            </span>
            <button type="button" className="text-brand underline" onClick={() => { removeFromCart(l.unit_id); void load(); }}>Remove</button>
          </li>
        ))}
        <li className="pt-2 font-display text-lg font-semibold">Total {formatRupees(total)}</li>
      </ul>
      {ok.length > 0 && (
        <form onSubmit={step === "cart" ? sendCode : confirm} className="grid gap-3">
          <Input aria-label="Full name" placeholder="Full name" required value={f.name} onChange={set("name")} disabled={step === "otp"} />
          <Input aria-label="Email" type="email" placeholder="Email (we send a code)" required value={f.email} onChange={set("email")} disabled={step === "otp"} />
          <Input aria-label="Phone" inputMode="tel" placeholder="Mobile number" required value={f.phone} onChange={set("phone")} disabled={step === "otp"} />
          <Input aria-label="Address" placeholder="Address" required value={f.address_line} onChange={set("address_line")} disabled={step === "otp"} />
          <Input aria-label="City" placeholder="City" required value={f.city} onChange={set("city")} disabled={step === "otp"} />
          <Input aria-label="PIN code" inputMode="numeric" placeholder="PIN code" required maxLength={6} value={f.pincode} onChange={(e) => { set("pincode")(e); void pin(e.target.value); }} disabled={step === "otp"} />
          {est && <p className="text-xs text-midnight/70">{est}</p>}
          {step === "otp" && <Input aria-label="6-digit code" inputMode="numeric" placeholder="6-digit code" required minLength={4} maxLength={8} value={otp} onChange={(e) => setOtp(e.target.value)} />}
          {demo && step === "otp" && <p className="text-xs text-midnight/60">Demo mode (no email service connected): your code is {demo}</p>}
          <Button type="submit" disabled={busy}>{busy ? "Please wait..." : step === "cart" ? "Send code" : "Hold for 15 minutes"}</Button>
        </form>
      )}
      {error && <p role="alert" className="text-sm text-red-700 md:col-span-2">{error}</p>}
    </div>
  );
}
