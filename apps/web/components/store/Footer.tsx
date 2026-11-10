import Link from "next/link";
import { Container } from "./Container";
import { isPreview } from "@/lib/config";

const COLS = [
  {
    title: "Shop",
    links: [
      ["All refurbished phones", "/refurbished-mobiles"],
      ["Under ₹20,000", "/refurbished-mobiles/under-20000"],
      ["Find a store", "/stores"],
      ["Exchange your phone", "/exchange"],
    ],
  },
  {
    title: "Trust",
    links: [
      ["Quality check", "/quality-check"],
      ["Grading", "/grading"],
      ["Warranty", "/warranty"],
      ["Returns", "/returns"],
    ],
  },
  {
    title: "Company",
    links: [
      ["About", "/about"],
      ["Contact", "/contact"],
      ["FAQ", "/faq"],
    ],
  },
];

export function Footer() {
  return (
    <footer className="mt-16 bg-midnight pb-24 pt-12 text-porcelain md:pb-12">
      <Container>
        <div className="grid gap-8 sm:grid-cols-2 md:grid-cols-4">
          <div>
            <div className="font-display text-xl font-bold lowercase">
              refurbi<span className="text-brand">.</span>
            </div>
            <p className="mt-2 max-w-xs text-sm text-silver">
              Refurbished smartphones, checked and graded, with the details you need before you buy.
            </p>
          </div>
          {COLS.map((c) => (
            <div key={c.title}>
              <div className="text-xs font-semibold uppercase tracking-wide text-silver">{c.title}</div>
              <ul className="mt-3 space-y-2 text-sm">
                {c.links.map(([label, href]) => (
                  <li key={href}>
                    <Link href={href} className="hover:text-brand">
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-10 flex flex-wrap justify-between gap-2 border-t border-white/10 pt-6 text-xs text-silver">
          <span>© Refurbi. Refurbished devices are pre-owned and are not new.</span>
          {isPreview() && <Link href="/preview" className="underline">Preview map</Link>}
        </div>
      </Container>
    </footer>
  );
}
