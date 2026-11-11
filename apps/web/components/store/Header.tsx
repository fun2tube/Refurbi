import Link from "next/link";
import { CartLink } from "./CartLink";
import { CondensingHeader } from "./CondensingHeader";
import { Container } from "./Container";

export const NAV = [
  { href: "/refurbished-mobiles", label: "Phones" },
  { href: "/stores", label: "Stores" },
  { href: "/exchange", label: "Exchange" },
  { href: "/quality-check", label: "Quality" },
  { href: "/warranty", label: "Warranty" },
];

export function Header() {
  return (
    <CondensingHeader>
      <Container className="flex h-14 items-center gap-4 md:h-16">
        <Link href="/" className="origin-left font-display text-xl font-bold lowercase transition-transform duration-200 group-data-[condensed=true]:scale-90">
          refurbi<span className="text-brand">.</span>
        </Link>
        <nav aria-label="Main" className="ml-4 hidden gap-5 text-sm font-medium md:flex">
          {NAV.map((n) => (
            <Link key={n.href} href={n.href} className="text-midnight/80 hover:text-brand">
              {n.label}
            </Link>
          ))}
        </nav>
        <form action="/refurbished-mobiles" role="search" className="ml-auto flex-1 md:max-w-xs">
          <label htmlFor="site-search" className="sr-only">
            Search phones
          </label>
          <input
            id="site-search"
            name="q"
            type="search"
            placeholder="Search iPhone 13, Galaxy S22..."
            className="h-10 w-full rounded-full border border-silver/60 bg-white px-4 text-sm outline-none focus:border-brand"
          />
        </form>
        <CartLink />
      </Container>
    </CondensingHeader>
  );
}
