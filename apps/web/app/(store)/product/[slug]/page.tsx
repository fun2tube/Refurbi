import type { Metadata } from "next";
import { FlipGallery } from "@/components/product/FlipGallery";
import { BatteryRing } from "@/components/product/BatteryRing";
import { ClipReveal, RevealItem } from "@/components/product/ClipReveal";
import { StickyBar } from "@/components/product/StickyBar";
import { ApiError } from "@/components/store/ApiError";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Container } from "@/components/store/Container";
import { JsonLd } from "@/components/store/JsonLd";
import { breadcrumbLd } from "@/lib/seo";
import { Faq, PRODUCT_FAQS } from "@/components/store/Faq";
import { apiBaseUrl } from "@/lib/config";
import { AddToCart } from "@/components/store/AddToCart";
import { ReserveButton } from "@/components/store/ReserveButton";
import { WhatsAppButton } from "@/components/store/WhatsAppButton";
import { GradeBadge, Price } from "@/components/ui";
import { getModel, getUnits, type Unit } from "@/lib/api";
import { formatRupees } from "@/lib/money";
import { siteUrl, whatsappLink } from "@/lib/site";

export const dynamic = "force-dynamic";
type Props = { params: Promise<{ slug: string }>; searchParams: Promise<{ storage?: string }> };

const SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const m = SLUG.test(slug) ? await getModel(slug) : null;
  if (!m || !m.ok) return { title: "Phone not found" };
  return {
    title: `Refurbished ${m.data.name}`,
    description: `Buy a checked, graded refurbished ${m.data.name}. See battery health, grade, price and store for every available unit.`,
    alternates: { canonical: `/refurbished-${slug}` },
  };
}

function jsonLd(name: string, slug: string, units: Unit[]) {
  const prices = units.map((u) => u.price_paise / 100);
  const url = `${siteUrl()}/refurbished-${slug}`;
  return {
    "@context": "https://schema.org",
    "@type": "Product",
    name: `Refurbished ${name}`,
    url,
    itemCondition: "https://schema.org/RefurbishedCondition",
    ...(units.length
      ? {
          offers: {
            "@type": "AggregateOffer",
            priceCurrency: "INR",
            lowPrice: Math.min(...prices),
            highPrice: Math.max(...prices),
            offerCount: units.length,
            availability: "https://schema.org/InStock",
            itemCondition: "https://schema.org/RefurbishedCondition",
          },
        }
      : {}),
  };
}

export default async function Page({ params, searchParams }: Props) {
  const { slug } = await params;
  const { storage } = await searchParams;
  if (!SLUG.test(slug)) notFound();
  const [model, units] = await Promise.all([getModel(slug), getUnits({ model: slug, sort: "price_asc", page_size: 50 })]);
  if (!model.ok) {
    if (model.error === "not_found") notFound();
    return <Container className="py-10"><ApiError error={model.error} waking={model.waking} /></Container>;
  }
  const m = model.data;
  const all = units.ok ? units.data.items : [];
  const storages = [...new Set(all.map((u) => u.storage_gb))].sort((a, b) => a - b);
  const sel = Number.parseInt(storage ?? "", 10);
  const list = Number.isFinite(sel) ? all.filter((u) => u.storage_gb === sel) : all;
  const from = all.length ? Math.min(...all.map((u) => u.price_paise)) : null;
  const msg = `Hi Refurbi, I'm interested in a refurbished ${m.name}. Is it available?`;
  const wa = whatsappLink(msg);
  const firstStore = list.find((u) => u.store)?.store;

  return (
    <>
      <JsonLd data={jsonLd(m.name, slug, all)} />
      <JsonLd data={breadcrumbLd([{ name: "Home", path: "/" }, { name: "Refurbished mobiles", path: "/refurbished-mobiles" }, { name: m.brand.name, path: `/refurbished-mobiles/${m.brand.slug}` }, { name: m.name, path: `/refurbished-${slug}` }])} />
      <Container className="py-6 md:py-10">
        <nav aria-label="Breadcrumb" className="text-xs text-midnight/60">
          <Link href="/">Home</Link> / <Link href="/refurbished-mobiles">Refurbished mobiles</Link> /{" "}
          <Link href={`/refurbished-mobiles/${m.brand.slug}`}>{m.brand.name}</Link>
        </nav>
        <div className="mt-4 grid gap-8 md:grid-cols-2">
          <FlipGallery
            seed={m.name.length}
            name={m.name}
            photos={[...new Set(all.flatMap((u) => u.photos))].slice(0, 4)}
            facts={[m.is_5g ? "5G" : "4G", ...(m.release_year ? [`Released ${m.release_year}`] : []), "Checked unit by unit", "Battery health shown"]}
          />
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-midnight/60">{m.brand.name}</div>
            <h1 className="font-display text-3xl font-bold">Refurbished {m.name}</h1>
            <p className="mt-1 text-sm text-midnight/70">
              {m.release_year ? `${m.release_year} · ` : ""}
              {m.is_5g ? "5G" : "4G"}
            </p>
            {from != null ? (
              <p className="mt-4">
                <span className="text-sm text-midnight/70">From </span>
                <Price paise={from} className="text-3xl" />
                <span className="ml-2 text-sm text-midnight/70">· {all.length} available</span>
              </p>
            ) : (
              <p className="mt-4 text-midnight/70">No units of this model are in stock right now. Ask us and we will look for one.</p>
            )}
            {m.description && <p className="mt-4 text-sm text-midnight/75">{m.description}</p>}
            <div className="mt-6 hidden gap-3 md:flex">
              <WhatsAppButton message={msg} label="Ask on WhatsApp" />
              {firstStore && (
                <Link href={`/stores/${firstStore.slug}`} className="inline-flex h-12 items-center rounded-full border border-silver px-6 font-medium">
                  Visit store
                </Link>
              )}
            </div>
          </div>
        </div>

        <section aria-labelledby="units" className="mt-12">
          <h2 id="units" className="font-display text-xl font-bold">
            Available units
          </h2>
          {storages.length > 1 && (
            <div className="mt-3 flex flex-wrap gap-2" role="group" aria-label="Storage">
              <Link href={`/refurbished-${slug}`} className={`rounded-full border px-4 py-1.5 text-sm ${!Number.isFinite(sel) ? "border-brand bg-brand/10 text-brand-dark" : "border-silver/60"}`}>All</Link>
              {storages.map((s) => (
                <Link key={s} href={`/refurbished-${slug}?storage=${s}`} className={`rounded-full border px-4 py-1.5 text-sm ${sel === s ? "border-brand bg-brand/10 text-brand-dark" : "border-silver/60"}`}>
                  {s} GB
                </Link>
              ))}
            </div>
          )}
          {list.length === 0 ? (
            <p className="mt-3 text-sm text-midnight/70">No units available.</p>
          ) : (
            <ul className="mt-3 space-y-3">
              {list.map((u, i) => (
                <RevealItem key={u.unit_id} index={i} className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-2xl border border-silver/40 bg-white p-4">
                  <div className="min-w-[9rem] flex-1">
                    <div className="font-display font-semibold">
                      {u.storage_gb} GB{u.ram_gb ? ` · ${u.ram_gb} GB RAM` : ""}
                    </div>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-midnight/70">
                      {u.grade && <GradeBadge grade={u.grade} />}
                      {u.battery_health != null ? <BatteryRing percent={u.battery_health} /> : null}
                      <span>{u.battery_health != null ? `Battery ${u.battery_health}%` : "Battery tested"}</span>
                    </div>
                    <div className="mt-1 text-sm text-midnight/70">
                      {u.store ? (
                        <Link href={`/stores/${u.store.slug}`} className="underline">
                          {u.store.name}, {u.store.city}
                        </Link>
                      ) : (
                        "Ships from Refurbi warehouse"
                      )}
                    </div>
                  </div>
                  <Price paise={u.price_paise} className="text-xl" />
                  <a
                    href={whatsappLink(`Hi Refurbi, I'm interested in the ${m.name} ${u.storage_gb}GB (Grade ${u.grade ?? "-"}, ${formatRupees(u.price_paise)}), listing #${u.unit_id}.`)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex h-10 items-center rounded-full bg-brand px-4 text-sm font-medium text-white hover:bg-brand-dark"
                  >
                    Ask about this phone
                  </a>
                  <AddToCart unitId={u.unit_id} />
                  <ReserveButton apiBase={apiBaseUrl()} unitId={u.unit_id} label="Reserve for store pickup" />
                </RevealItem>
              ))}
            </ul>
          )}
        </section>

        {m.specifications.length > 0 && (
          <section aria-labelledby="specs" className="mt-12">
            <h2 id="specs" className="font-display text-xl font-bold">
              Specifications
            </h2>
            <ClipReveal className="mt-3">
            <dl className="divide-y divide-silver/40 rounded-2xl border border-silver/40 bg-white">
              {m.specifications.map((s) => (
                <div key={s.key} className="grid grid-cols-2 gap-3 p-3 text-sm">
                  <dt className="text-midnight/60">{s.key}</dt>
                  <dd>{s.value}</dd>
                </div>
              ))}
            </dl>
            </ClipReveal>
          </section>
        )}

        <section aria-labelledby="warranty" className="mt-12 rounded-2xl bg-white p-5">
          <h2 id="warranty" className="font-display text-xl font-bold">
            Warranty and returns
          </h2>
          <p className="mt-2 text-sm text-midnight/75">
            Warranty and return terms are set out on our <Link href="/warranty" className="underline">warranty</Link> and{" "}
            <Link href="/returns" className="underline">returns</Link> pages and apply as stated on your invoice.
          </p>
        </section>

        <div className="mt-12">
          <Faq items={PRODUCT_FAQS} />
        </div>
      </Container>

      {/* Sticky CTA: sits above the mobile bottom nav */}
      <StickyBar>
        <a href={wa} target="_blank" rel="noopener noreferrer" className="inline-flex h-11 flex-1 items-center justify-center rounded-full bg-brand text-sm font-medium text-white">
          WhatsApp
        </a>
        <Link href={firstStore ? `/stores/${firstStore.slug}` : "/stores"} className="inline-flex h-11 flex-1 items-center justify-center rounded-full border border-silver text-sm font-medium">
          Visit store
        </Link>
      </StickyBar>
    </>
  );
}
