import Link from "next/link";
import { Container } from "@/components/store/Container";
import { DeviceArt } from "@/components/store/DeviceArt";
import { UnitGrid } from "@/components/store/UnitCard";
import { WhatsAppButton } from "@/components/store/WhatsAppButton";
import { JsonLd } from "@/components/store/JsonLd";
import { organizationLd, websiteLd } from "@/lib/seo";
import { PreviewMap } from "@/components/store/PreviewMap";
import { getBrands, getModels, getUnits } from "@/lib/api";
import { formatRupees } from "@/lib/money";
import { isPreview } from "@/lib/config";

export const dynamic = "force-dynamic";

const TRUST = [
  { t: "Checked device by device", d: "Every phone goes through a multi-point functional check before it is listed." },
  { t: "Battery health shown", d: "You see the battery percentage of the exact phone you are buying." },
  { t: "Graded honestly", d: "Grade A, B or C describes cosmetic condition. See how we grade." },
  { t: "Warranty and invoice", d: "A proper invoice with every phone. Warranty terms are shown on each listing." },
];

const BUDGETS = [10000, 15000, 20000, 30000];

export default async function Home() {
  const [units, models, brands] = await Promise.all([
    getUnits({ page_size: 8, sort: "newest" }),
    getModels({ limit: 8 }),
    getBrands(),
  ]);
  const hero = units.ok ? units.data.items[0] : undefined;

  return (
    <>
      <JsonLd data={organizationLd()} />
      <JsonLd data={websiteLd()} />
      <section className="bg-midnight text-porcelain">
        <Container className="grid items-center gap-6 py-10 md:grid-cols-2 md:py-16">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-silver">Refurbished smartphones</p>
            <h1 className="mt-3 font-display text-4xl font-bold leading-tight md:text-5xl">
              The phone you want, checked and graded.
            </h1>
            <p className="mt-4 max-w-md text-silver">
              Real units, real battery health, real price. See exactly which phone you are getting, and pick it up
              from a store near you.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link
                href="/refurbished-mobiles"
                className="inline-flex h-12 items-center rounded-full bg-brand px-6 font-medium text-white hover:bg-brand-dark"
              >
                Browse phones
              </Link>
              <Link
                href="/stores"
                className="inline-flex h-12 items-center rounded-full border border-silver/60 px-6 font-medium hover:bg-white/10"
              >
                Find a store
              </Link>
              <Link
                href="/exchange"
                className="inline-flex h-12 items-center rounded-full border border-silver/60 px-6 font-medium hover:bg-white/10"
              >
                Exchange your phone
              </Link>
            </div>
          </div>
          <div className="relative mx-auto flex h-64 items-end justify-center md:h-96">
            <div className="absolute inset-x-6 bottom-4 top-10 rounded-full bg-brand/20 blur-3xl" aria-hidden />
            <DeviceArt seed={1} className="relative -rotate-3 motion-safe:animate-[float_6s_ease-in-out_infinite]" />
            {hero && (
              <Link
                href={`/refurbished-${hero.model.slug}`}
                className="absolute bottom-2 right-0 rounded-2xl bg-porcelain px-4 py-3 text-midnight shadow-xl md:right-6"
              >
                <div className="text-[11px] uppercase tracking-wide text-silver">In stock now</div>
                <div className="font-display text-sm font-semibold">{hero.model.name}</div>
                <div className="font-display text-lg font-bold text-brand">from {formatRupees(hero.price_paise)}</div>
              </Link>
            )}
          </div>
        </Container>
      </section>

      <Container className="mt-10 space-y-12">
        <section aria-labelledby="budget">
          <h2 id="budget" className="font-display text-xl font-bold">
            Shop by budget
          </h2>
          <ul className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {BUDGETS.map((b) => (
              <li key={b}>
                <Link
                  href={`/refurbished-mobiles/under-${b}`}
                  className="block rounded-2xl border border-silver/40 bg-white p-4 text-center font-display font-semibold hover:border-brand"
                >
                  Under {formatRupees(b * 100)}
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="fresh">
          <div className="flex items-end justify-between">
            <h2 id="fresh" className="font-display text-xl font-bold">
              Available now
            </h2>
            <Link href="/refurbished-mobiles" className="text-sm font-medium text-brand">
              View all
            </Link>
          </div>
          <div className="mt-3">
            {units.ok ? (
              units.data.items.length ? (
                <UnitGrid units={units.data.items} />
              ) : (
                <p className="text-sm text-midnight/70">No phones are listed right now. Please check back soon.</p>
              )
            ) : (
              <p className="text-sm text-midnight/70">{units.error}</p>
            )}
          </div>
        </section>

        {brands.ok && brands.data.length > 0 && (
          <section aria-labelledby="brands">
            <h2 id="brands" className="font-display text-xl font-bold">
              Shop by brand
            </h2>
            <ul className="mt-3 flex flex-wrap gap-2">
              {brands.data.map((b) => (
                <li key={b.slug}>
                  <Link
                    href={`/refurbished-mobiles/${b.slug}`}
                    className="inline-block rounded-full border border-silver/60 bg-white px-5 py-2 text-sm font-medium hover:border-brand"
                  >
                    {b.name}
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}

        {models.ok && models.data.length > 0 && (
          <section aria-labelledby="models">
            <h2 id="models" className="font-display text-xl font-bold">
              Popular models
            </h2>
            <ul className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-4">
              {models.data.map((m) => (
                <li key={m.slug}>
                  <Link
                    href={`/refurbished-${m.slug}`}
                    className="block rounded-2xl border border-silver/40 bg-white p-4 hover:border-brand"
                  >
                    <div className="text-[11px] uppercase tracking-wide text-silver">{m.brand.name}</div>
                    <div className="font-display font-semibold">{m.name}</div>
                    <div className="mt-1 text-sm text-midnight/70">
                      From {formatRupees(m.from_price_paise)} · {m.units_available} in stock
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}

        <section aria-labelledby="trust" className="rounded-3xl bg-white p-6 md:p-10">
          <h2 id="trust" className="font-display text-xl font-bold">
            Why buy from Refurbi
          </h2>
          <ul className="mt-4 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {TRUST.map((t) => (
              <li key={t.t}>
                <div className="font-display font-semibold text-brand">{t.t}</div>
                <p className="mt-1 text-sm text-midnight/70">{t.d}</p>
              </li>
            ))}
          </ul>
          <Link href="/quality-check" className="mt-5 inline-block text-sm font-medium text-brand">
            How we check phones →
          </Link>
        </section>

        <section className="rounded-3xl bg-brand p-6 text-white md:flex md:items-center md:justify-between md:p-10">
          <div>
            <h2 className="font-display text-xl font-bold">Not sure which phone? Ask us.</h2>
            <p className="mt-1 text-white/80">Tell us your budget and we will suggest what is in stock.</p>
          </div>
          <WhatsAppButton
            message="Hi Refurbi, I'd like help choosing a refurbished phone."
            className="mt-4 bg-midnight hover:bg-black md:mt-0"
          />
        </section>

        {isPreview() && <PreviewMap />}
      </Container>
    </>
  );
}
