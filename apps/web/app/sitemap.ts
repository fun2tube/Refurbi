import type { MetadataRoute } from "next";
import { getBrands, getModels, getStores } from "@/lib/api";
import { PAGES } from "@/lib/content";
import { siteUrl } from "@/lib/site";

export const dynamic = "force-dynamic";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = siteUrl();
  const [brands, models, stores] = await Promise.all([getBrands(), getModels({ limit: 100 }), getStores()]);
  const paths = ["/", "/refurbished-mobiles", "/stores", "/exchange", ...PAGES.map((p) => `/${p.slug}`)];
  if (brands.ok) paths.push(...brands.data.map((b) => `/refurbished-mobiles/${b.slug}`));
  if (models.ok) paths.push(...models.data.map((m) => `/refurbished-${m.slug}`));
  if (stores.ok) paths.push(...stores.data.map((s) => `/stores/${s.slug}`));
  paths.push("/refurbished-mobiles/under-10000", "/refurbished-mobiles/under-15000", "/refurbished-mobiles/under-20000", "/refurbished-mobiles/under-30000");
  return [...new Set(paths)].map((p) => ({ url: `${base}${p === "/" ? "" : p}`, changeFrequency: "daily" as const }));
}
