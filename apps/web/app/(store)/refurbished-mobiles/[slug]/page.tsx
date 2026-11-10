import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Listing } from "@/components/store/Listing";
import { parseListingSlug, type SP } from "@/lib/listing";
import { getBrands } from "@/lib/api";
import { formatRupees } from "@/lib/money";

export const dynamic = "force-dynamic";
type Props = { params: Promise<{ slug: string }>; searchParams: Promise<SP> };

type Resolved = { title: string; fixed: Record<string, string>; hide: string[] };

async function resolve(slug: string): Promise<Resolved | null> {
  const parsed = parseListingSlug(slug);
  if (!parsed) return null;
  if (parsed.kind === "budget") {
    const t = `Refurbished phones under ${formatRupees(parsed.rupees * 100)}`;
    return { title: t, fixed: { max_price: String(parsed.rupees) }, hide: ["max_price"] };
  }
  const brands = await getBrands();
  const b = brands.ok ? brands.data.find((x) => x.slug === parsed.slug) : undefined;
  if (!b) return brands.ok ? null : { title: `Refurbished ${parsed.slug} phones`, fixed: { brand: parsed.slug }, hide: ["brand"] };
  return { title: `Refurbished ${b.name} phones`, fixed: { brand: b.slug }, hide: ["brand"] };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const r = await resolve(slug);
  if (!r) return { title: "Not found" };
  return {
    title: r.title,
    description: `${r.title}: checked and graded phones with battery health and price shown per phone.`,
    alternates: { canonical: `/refurbished-mobiles/${slug}` },
  };
}

export default async function Page({ params, searchParams }: Props) {
  const { slug } = await params;
  const r = await resolve(slug);
  if (!r) notFound();
  return <Listing basePath={`/refurbished-mobiles/${slug}`} title={r.title} fixed={r.fixed} hide={r.hide} sp={await searchParams} />;
}
