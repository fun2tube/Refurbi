import Link from "next/link";
import { apiBaseUrl } from "@/lib/config";
import { PosApp } from "./PosApp";

export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <div className="space-y-3">
      <h1 className="font-display text-2xl font-bold">Counter POS</h1>
      <p className="text-sm text-midnight/70">
        Sell a device from your counter stock. Demo sign-in: partner@demo.refurbi (same password as the demo admin) at{" "}
        <Link className="underline" href="/admin/login">/admin/login</Link>.
      </p>
      <PosApp apiBase={apiBaseUrl()} />
    </div>
  );
}
