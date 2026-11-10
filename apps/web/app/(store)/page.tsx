import Link from "next/link";
import { Card } from "@/components/ui";

// Preview start page. The real storefront homepage is T21 and will replace this.
const AREAS: { title: string; blurb: string; href?: string }[] = [
  { title: "Store catalogue", blurb: "Browse the demo catalogue from the public API.", href: "/catalogue" },
  { title: "Admin", blurb: "Back-office. Sign in with the demo admin account.", href: "/admin" },
  { title: "Partner", blurb: "Counter area (POS comes later).", href: "/partner" },
  { title: "Storefront pages, reserve & store locator", blurb: "Coming soon." },
  { title: "Inventory, QC and pricing screens", blurb: "Coming soon." },
  { title: "Counter POS, invoices and warranty", blurb: "Coming soon." },
];

export default function Home() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-bold">Refurbi preview</h1>
        <p className="mt-1 text-midnight/70">
          Early build for review. Everything shown is demo data.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {AREAS.map((a) => {
          const body = (
            <Card className="h-full space-y-1">
              <div className="font-display text-lg font-semibold">{a.title}</div>
              <div className="text-sm text-midnight/70">{a.blurb}</div>
              {!a.href && <div className="text-xs uppercase tracking-wide text-silver">Coming soon</div>}
            </Card>
          );
          return a.href ? (
            <Link key={a.title} href={a.href} className="block hover:opacity-90">
              {body}
            </Link>
          ) : (
            <div key={a.title} className="opacity-70">
              {body}
            </div>
          );
        })}
      </div>
    </div>
  );
}
