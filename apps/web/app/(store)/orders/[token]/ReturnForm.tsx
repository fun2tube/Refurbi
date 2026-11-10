"use client";
import { useState } from "react";
import { Button, Input } from "@/components/ui";

export function ReturnForm({ apiBase, token, invoice }: { apiBase: string; token: string; invoice: string }) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [msg, setMsg] = useState("");
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const r = await fetch(`${apiBase}/public/orders/${token}/returns`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ invoice_number: invoice, reason }),
      });
      if (r.ok) return setMsg("Return requested. We will contact you by email.");
      setMsg(r.status === 409 ? "Returns open once the order is delivered (or one was already requested)." : r.status === 400 ? "The return window for this order has closed." : "Could not submit - please retry.");
    } catch { setMsg("Could not reach the server - please retry."); }
  }
  if (!open) return <button type="button" className="ml-2 text-brand underline" onClick={() => setOpen(true)}>Request return</button>;
  return (
    <form onSubmit={submit} className="mt-2 grid max-w-sm gap-2">
      <Input aria-label="Reason for return" placeholder="Reason for return" required minLength={3} maxLength={500} value={reason} onChange={(e) => setReason(e.target.value)} />
      <Button type="submit">Submit return request</Button>
      {msg && <p role="status" className="text-xs">{msg}</p>}
    </form>
  );
}
