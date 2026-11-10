import Link from "next/link";
import { Card } from "@/components/ui";

/** Preview-only index of every page built so far (demo data). Update as tasks land. */
export const PREVIEW_PAGES: { title: string; blurb: string; href: string }[] = [
  { title: "Homepage", blurb: "This page.", href: "/" },
  { title: "All refurbished phones", blurb: "Filterable listing of real units (brand, price, storage, RAM, grade, battery, 5G, store).", href: "/refurbished-mobiles" },
  { title: "Brand listing", blurb: "Apple phones, with crawlable pagination.", href: "/refurbished-mobiles/apple" },
  { title: "Budget listing", blurb: "Phones under ₹20,000.", href: "/refurbished-mobiles/under-20000" },
  { title: "Old catalogue (API check)", blurb: "Raw model list from the public API.", href: "/catalogue" },
  { title: "Admin", blurb: "Back-office. Demo admin sign-in.", href: "/admin" },
  { title: "Partner", blurb: "Counter area (POS comes later).", href: "/partner" },
];

export function PreviewMap() {
  return (
    <section aria-labelledby="pmap">
      <h2 id="pmap" className="font-display text-xl font-bold">
        Preview map <span className="text-sm font-normal text-silver">(demo only)</span>
      </h2>
      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {PREVIEW_PAGES.map((p) => (
          <Link key={p.href} href={p.href} className="block hover:opacity-90">
            <Card className="h-full space-y-1">
              <div className="font-display font-semibold">{p.title}</div>
              <div className="text-sm text-midnight/70">{p.blurb}</div>
              <div className="text-xs text-silver">{p.href}</div>
            </Card>
          </Link>
        ))}
      </div>
    </section>
  );
}
