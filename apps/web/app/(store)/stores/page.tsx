import type { Metadata } from "next";
import { ApiError } from "@/components/store/ApiError";
import Link from "next/link";
import { Container } from "@/components/store/Container";
import { WhatsAppButton } from "@/components/store/WhatsAppButton";
import { getStores } from "@/lib/api";

export const dynamic = "force-dynamic";
export const metadata: Metadata = {
  title: "Find a Refurbi store",
  description: "See phones in stock at stores near you, then visit to check them in person.",
  alternates: { canonical: "/stores" },
};

export default async function Stores() {
  const res = await getStores();
  return (
    <Container className="py-6 md:py-10">
      <h1 className="font-display text-2xl font-bold md:text-3xl">Find a store</h1>
      <p className="mt-1 max-w-2xl text-sm text-midnight/70">
        Stock shown at each store is live. Visit to see a phone in person, or message us first.
      </p>
      {!res.ok ? (
        <div className="mt-6"><ApiError error={res.error} waking={res.waking} /></div>
      ) : res.data.length === 0 ? (
        <p className="mt-6 text-sm text-midnight/70">Stores will be listed here soon.</p>
      ) : (
        <ul className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {res.data.map((s) => (
            <li key={s.slug}>
              <Link href={`/stores/${s.slug}`} className="block h-full rounded-2xl border border-silver/40 bg-white p-5 hover:border-brand">
                <div className="font-display text-lg font-semibold">{s.name}</div>
                <div className="text-sm text-midnight/70">{s.city}</div>
                {s.is_demo && <div className="mt-1 text-[11px] uppercase tracking-wide text-silver">Demo store</div>}
                <div className="mt-3 text-sm font-medium text-brand">
                  {s.units_available} phone{s.units_available === 1 ? "" : "s"} in stock →
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
      <div className="mt-10">
        <WhatsAppButton message="Hi Refurbi, which store is nearest to me?" label="Ask which store is nearest" />
      </div>
    </Container>
  );
}
