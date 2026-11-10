"use client";

import Link from "next/link";
import { useState } from "react";
import { Button, Input } from "@/components/ui";

type Me = { email: string; roles: { code: string }[] };

export function LoginForm({ apiBase }: { apiBase: string }) {
  const [email, setEmail] = useState("admin@demo.refurbi");
  const [password, setPassword] = useState("");
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res = await fetch(`${apiBase}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        setError(res.status === 401 ? "Wrong email or password." : `Sign-in failed (${res.status}).`);
        return;
      }
      const body = await res.json();
      try {
        sessionStorage.setItem("refurbi_access_token", body.access_token);
      } catch {}
      setMe(body.user);
    } catch {
      setError("Could not reach the API (it may be waking up - retry in a minute).");
    } finally {
      setBusy(false);
    }
  }

  if (me) {
    return (
      <p className="rounded-lg border border-silver/40 bg-white p-4 text-sm">
        Signed in as <strong>{me.email}</strong> ({me.roles.map((r) => r.code).join(", ")}). Open the{" "}
        <Link className="underline" href="/admin">admin home</Link> or the <Link className="underline" href="/partner">counter POS</Link>.
      </p>
    );
  }
  return (
    <form onSubmit={submit} className="space-y-3">
      <label className="block text-sm">
        Email
        <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </label>
      <label className="block text-sm">
        Password
        <Input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </label>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <Button type="submit" disabled={busy}>
        {busy ? "Signing in..." : "Sign in"}
      </Button>
    </form>
  );
}
