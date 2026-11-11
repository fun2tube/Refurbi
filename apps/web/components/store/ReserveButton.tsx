"use client";

import { useState } from "react";
import { SuccessBurst } from "@/components/motion/SuccessBurst";
import { Button, Input } from "@/components/ui";

type Done = { code: string; expires_at: string; store_name: string | null; store_city: string | null };

/** Reserve a unit for store pickup: email OTP -> 24h hold. Pay at the store. */
export function ReserveButton({ apiBase, unitId, label }: { apiBase: string; unitId: number; label: string }) {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<"details" | "otp" | "done">("details");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [demo, setDemo] = useState("");
  const [done, setDone] = useState<Done | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function post(path: string, body: unknown) {
    return fetch(`${apiBase}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  }
  const fail = (s: number) =>
    setError(
      s === 429 ? "Too many attempts - please wait a few minutes."
      : s === 404 ? "Sorry, this phone was just taken or is no longer available."
      : s === 400 ? "That code is wrong or expired."
      : "Please check your details and try again.",
    );

  async function sendCode(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const r = await post("/public/reservations/otp", { email });
      if (!r.ok) return fail(r.status);
      const j = await r.json();
      setDemo(j.demo_code ?? "");
      setStep("otp");
    } catch {
      setError("Could not reach the server (it may be waking up) - please retry in a minute.");
    } finally {
      setBusy(false);
    }
  }

  async function confirm(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const r = await post("/public/reservations", { unit_id: unitId, name, email, otp });
      if (!r.ok) return fail(r.status);
      setDone(await r.json());
      setStep("done");
    } catch {
      setError("Could not reach the server - please retry.");
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button type="button" onClick={() => setOpen(true)} className="inline-flex h-10 items-center rounded-full border border-brand px-4 text-sm font-medium text-brand hover:bg-brand/5">
        {label}
      </button>
    );
  }
  return (
    <div className="basis-full rounded-xl bg-porcelain p-4" role="group" aria-label="Reserve for store pickup">
      {step === "details" && (
        <form onSubmit={sendCode} className="grid gap-3 sm:grid-cols-2">
          <Input aria-label="Your name" placeholder="Your name" required value={name} onChange={(e) => setName(e.target.value)} />
          <Input aria-label="Email" type="email" placeholder="Email (we send a code)" required value={email} onChange={(e) => setEmail(e.target.value)} />
          <p className="text-xs text-midnight/60 sm:col-span-2">We hold the phone for 24 hours. You pay at the store; nothing is charged online.</p>
          <Button type="submit" disabled={busy}>{busy ? "Sending..." : "Send code"}</Button>
        </form>
      )}
      {step === "otp" && (
        <form onSubmit={confirm} className="grid gap-3 sm:grid-cols-2">
          <Input aria-label="6-digit code" inputMode="numeric" placeholder="6-digit code" required minLength={4} maxLength={8} value={otp} onChange={(e) => setOtp(e.target.value)} />
          <Button type="submit" disabled={busy}>{busy ? "Reserving..." : "Reserve for 24 hours"}</Button>
          {demo && <p className="text-xs text-midnight/60 sm:col-span-2">Demo mode (no email service connected): your code is {demo}</p>}
        </form>
      )}
      {step === "done" && done && (
        <div role="status">
          <SuccessBurst />
          <p className="font-display font-semibold">Reserved! Your code: {done.code}</p>
          <p className="mt-1 text-sm text-midnight/70">
            Held at {done.store_name ? `${done.store_name}, ${done.store_city}` : "our pickup point"} until {new Date(done.expires_at).toLocaleString("en-IN")}. Show this code and pay at the store.
          </p>
        </div>
      )}
      {error && <p role="alert" className="mt-2 text-sm text-red-700">{error}</p>}
    </div>
  );
}
