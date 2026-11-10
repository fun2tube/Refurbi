"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Card } from "@/components/ui";
import { adminFetch } from "@/components/admin/api";

type Alert = { kind: string; severity: string; device_id: number; label: string; message: string };
type Res = { counts: Record<string, number>; total: number; items: Alert[] };

const TITLES: Record<string, string> = {
  AGEING_WARN: "Ageing 21+ days",
  AGEING_CRITICAL: "Ageing 35+ days",
  QC_FAILED: "QC failed",
  TRANSIT_STUCK: "Stuck in transit",
  COUNTER_MISMATCH: "Counter mismatch",
};

export function AlertsCard({ apiBase }: { apiBase: string }) {
  const [res, setRes] = useState<Res | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    void adminFetch<Res>(apiBase, "/admin/inventory/alerts").then((r) => (r.ok ? setRes(r.data) : setError(r.error)));
  }, [apiBase]);
  return (
    <Card className="space-y-2">
      <h2 className="font-display font-semibold">Stock alerts</h2>
      {error && <p className="text-sm text-midnight/60">{error} <Link href="/admin/login" className="text-brand underline">Sign in</Link></p>}
      {res && res.total === 0 && <p className="text-sm text-midnight/60">No alerts. Stock looks healthy.</p>}
      {res && res.total > 0 && (
        <>
          <p className="flex flex-wrap gap-2 text-xs">
            {Object.entries(res.counts).map(([k, n]) => <span key={k} className="rounded-full bg-porcelain px-2 py-0.5">{TITLES[k] ?? k}: {n}</span>)}
          </p>
          <ul className="space-y-1 text-sm">
            {res.items.slice(0, 15).map((a, i) => (
              <li key={i}>
                <span className={a.severity === "critical" ? "font-semibold text-red-700" : "font-semibold text-amber-700"}>{TITLES[a.kind] ?? a.kind}</span>{" "}
                <Link className="text-brand underline" href={`/admin/inventory/${a.device_id}`}>{a.label}</Link> - {a.message}
              </li>
            ))}
          </ul>
        </>
      )}
    </Card>
  );
}
