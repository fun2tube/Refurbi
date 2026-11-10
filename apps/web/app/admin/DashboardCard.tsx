"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Card } from "@/components/ui";
import { adminFetch } from "@/components/admin/api";

type Agg = { units: number; sales_paise: number; gross_margin_paise: number };
type Dash = {
  today: Agg;
  month: Agg;
  stock_by_location: { location: string; units: number }[];
  ageing: { bucket: string; units: number }[];
  counter_leaderboard: { counter_id: number; counter: string; units: number; sales_paise: number }[];
};

const rs = (p: number) => `Rs ${Math.round(p / 100).toLocaleString("en-IN")}`;

export function DashboardCard({ apiBase }: { apiBase: string }) {
  const [d, setD] = useState<Dash | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    void adminFetch<Dash>(apiBase, "/admin/dashboard").then((r) => (r.ok ? setD(r.data) : setError(r.error)));
  }, [apiBase]);
  if (error)
    return (
      <Card>
        <p className="text-sm text-midnight/60">{error} <Link href="/admin/login" className="text-brand underline">Sign in</Link></p>
      </Card>
    );
  if (!d) return <Card><p className="text-sm text-midnight/60">Loading dashboard...</p></Card>;
  const tiles: [string, string][] = [
    ["Today's sales", rs(d.today.sales_paise)],
    ["Units today", String(d.today.units)],
    ["Gross margin today", rs(d.today.gross_margin_paise)],
    ["Margin this month", rs(d.month.gross_margin_paise)],
  ];
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {tiles.map(([t, v]) => (
          <Card key={t} className="space-y-1">
            <div className="text-xs text-midnight/60">{t}</div>
            <div className="font-display text-xl font-bold">{v}</div>
          </Card>
        ))}
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <Card className="space-y-1">
          <h2 className="font-display font-semibold">Stock by location</h2>
          {d.stock_by_location.length === 0 && <p className="text-sm text-midnight/60">No sellable stock.</p>}
          {d.stock_by_location.map((s) => <p key={s.location} className="text-sm">{s.location}: <b>{s.units}</b></p>)}
        </Card>
        <Card className="space-y-1">
          <h2 className="font-display font-semibold">Stock ageing (days)</h2>
          {d.ageing.map((a) => <p key={a.bucket} className="text-sm">{a.bucket}: <b>{a.units}</b></p>)}
        </Card>
        <Card className="space-y-1">
          <h2 className="font-display font-semibold">Counter leaderboard (month)</h2>
          {d.counter_leaderboard.length === 0 && <p className="text-sm text-midnight/60">No counter sales yet.</p>}
          {d.counter_leaderboard.map((c, i) => <p key={c.counter_id} className="text-sm">{i + 1}. {c.counter}: {c.units} units, {rs(c.sales_paise)}</p>)}
        </Card>
      </div>
    </div>
  );
}
