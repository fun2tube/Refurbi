import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Container } from "@/components/store/Container";
import { MapPanel } from "@/components/store/MapPanel";
import { UnitGrid } from "@/components/store/UnitCard";
import { WhatsAppButton } from "@/components/store/WhatsAppButton";
import { apiGet, getUnits, type Store } from "@/lib/api";

export const dynamic = "force-dynamic";
type Props = { params: Promise<{ slug: string }> };
const SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/;

const load = (slug: string) => (SLUG.test(slug) ? apiGet<Store>(`/public/stores/${slug}`) : Promise.resolve(null));

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const s = await load(slug);
  if (!s || !s.ok) return { title: "Store not found" };
  return {
    title: `${s.data.name}, ${s.data.city}`,
    description: `Refurbished phones in stock at ${s.data.name}, ${s.data.city}.`,
    alternates: { canonical: `/stores/${slug}` },
  };
}

export default async function StorePage({ params }: Props) {
  const { slug } = await params;
  const store = await load(slug);
  if (!store) notFound();
  if (!store.ok) {
    if (store.error === "not_found") notFound();
    return <Container className="py-10"><p className="text-sm text-midnight/70">{store.error}</p></Container>;
  }
  const s = store.data;
  const units = await getUnits({ store: slug, page_size: 24, sort: "price_asc" });
  return (
    <Container className="py-6 md:py-10">
      <nav aria-label="Breadcrumb" className="text-xs text-midnight/60">
        <Link href="/">Home</Link> / <Link href="/stores">Stores</Link>
      </nav>
      <h1 className="mt-2 font-display text-2xl font-bold md:text-3xl">{s.name}</h1>
      <p className="text-sm text-midnight/70">
        {s.city}
        {s.is_demo && " · Demo store (placeholder data)"}
      </p>
      <div className="mt-6 grid gap-6 md:grid-cols-[1fr_20rem]">
        <MapPanel name={s.name} city={s.city} />
        <div className="space-y-3 rounded-2xl border border-silver/40 bg-white p-5 text-sm">
          <div>
            <div className="font-medium">Opening hours</div>
            <div className="text-midnight/70">To be confirmed. Message us to check before you visit.</div>
          </div>
          <div>
            <div className="font-medium">Address</div>
            <div className="text-midnight/70">Shown once the store is verified.</div>
          </div>
          <WhatsAppButton message={`Hi Refurbi, I'd like to visit ${s.name}, ${s.city}.`} label="Message on WhatsApp" className="w-full" />
        </div>
      </div>
      <h2 className="mt-10 font-display text-xl font-bold">In stock here ({s.units_available})</h2>
      <div className="mt-3">
        {units.ok && units.data.items.length > 0 ? (
          <UnitGrid units={units.data.items} />
        ) : (
          <p className="text-sm text-midnight/70">{units.ok ? "No phones in stock here right now." : units.error}</p>
        )}
      </div>
    </Container>
  );
}
