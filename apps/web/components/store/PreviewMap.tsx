import Link from "next/link";
import { Card } from "@/components/ui";

/** Preview-only index of every page built so far (demo data). Update as tasks land. */
export const PREVIEW_PAGES: { title: string; blurb: string; href: string }[] = [
  { title: "Homepage", blurb: "This page.", href: "/" },
  { title: "All refurbished phones", blurb: "Filterable listing of real units (brand, price, storage, RAM, grade, battery, 5G, store).", href: "/refurbished-mobiles" },
  { title: "Brand listing", blurb: "Apple phones, with crawlable pagination.", href: "/refurbished-mobiles/apple" },
  { title: "Budget listing", blurb: "Phones under ₹20,000.", href: "/refurbished-mobiles/under-20000" },
  { title: "Product page", blurb: "Model page listing the actual available units, specs, FAQs, sticky CTA.", href: "/refurbished-iphone-13" },
  { title: "Store locator", blurb: "Stores with live stock counts.", href: "/stores" },
  { title: "Store page", blurb: "Store detail with live stock, map adapter placeholder, WhatsApp.", href: "/stores/demo-counter-a" },
  { title: "Exchange enquiry", blurb: "Questionnaire -> indicative demo range -> lead saved.", href: "/exchange" },
  { title: "Quality check", blurb: "Trust page.", href: "/quality-check" },
  { title: "Grading", blurb: "Trust page.", href: "/grading" },
  { title: "Warranty", blurb: "Trust page.", href: "/warranty" },
  { title: "Returns", blurb: "Trust page.", href: "/returns" },
  { title: "About", blurb: "Trust page.", href: "/about" },
  { title: "Contact", blurb: "Trust page.", href: "/contact" },
  { title: "FAQ", blurb: "Trust page.", href: "/faq" },
  { title: "sitemap.xml", blurb: "Generated from live brands, models and stores.", href: "/sitemap.xml" },
  { title: "robots.txt", blurb: "Preview blocks all crawlers.", href: "/robots.txt" },
  { title: "Old catalogue (API check)", blurb: "Raw model list from the public API.", href: "/catalogue" },
  { title: "Admin", blurb: "Back-office home. Demo admin sign-in.", href: "/admin" },
  { title: "Admin: inventory", blurb: "Device table with filters; device page has timeline, QC form, pricing, photos.", href: "/admin/inventory" },
  { title: "Admin: receive stock", blurb: "Suppliers, purchase orders, goods receipt with IMEI check.", href: "/admin/receive" },
  { title: "Admin: exchange enquiries", blurb: "Lead inbox with status.", href: "/admin/exchange" },
  { title: "Partner", blurb: "Counter POS: search counter stock, sell, payment mode, invoice PDF, WhatsApp share. Sign in as partner@demo.refurbi.", href: "/partner" },
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
