import Link from "next/link";
import { JsonLd } from "./JsonLd";
import { breadcrumbLd } from "@/lib/seo";
import { Container } from "./Container";
import { UnitGrid } from "./UnitCard";
import { cleanFilters, pageNumber, type SP } from "@/lib/listing";
import { getBrands, getStores, getUnits, qs } from "@/lib/api";
import { formatRupees } from "@/lib/money";

function apiParams(f: Record<string, string>, fixed: Record<string, string>, page: number) {
  const p: Record<string, string | number | undefined> = { ...f, ...fixed, page, page_size: 12 };
  // UI works in rupees; API in paise.
  const mp = Number.parseInt(String(p.max_price ?? ""), 10);
  p.max_price = Number.isFinite(mp) && mp > 0 ? mp * 100 : undefined;
  return p;
}

const sel = "h-10 w-full rounded-lg border border-silver/60 bg-white px-2 text-sm";

export async function Listing({
  basePath,
  title,
  intro,
  fixed = {},
  hide = [],
  sp,
}: {
  basePath: string;
  title: string;
  intro?: string;
  fixed?: Record<string, string>;
  hide?: string[];
  sp: SP;
}) {
  const f = cleanFilters(sp);
  const page = pageNumber(sp);
  const [res, brands, stores] = await Promise.all([getUnits(apiParams(f, fixed, page)), getBrands(), getStores()]);
  const link = (p: number) => `${basePath}${qs({ ...f, page: p > 1 ? p : undefined })}`;
  const show = (k: string) => !hide.includes(k);

  return (
    <Container className="py-6 md:py-10">
      <JsonLd data={breadcrumbLd([{ name: "Home", path: "/" }, { name: "Refurbished mobiles", path: "/refurbished-mobiles" }, ...(basePath !== "/refurbished-mobiles" ? [{ name: title, path: basePath }] : [])])} />
      <nav aria-label="Breadcrumb" className="text-xs text-midnight/60">
        <Link href="/">Home</Link> / <Link href="/refurbished-mobiles">Refurbished mobiles</Link>
        {basePath !== "/refurbished-mobiles" && <> / <span>{title}</span></>}
      </nav>
      <h1 className="mt-2 font-display text-2xl font-bold md:text-3xl">{title}</h1>
      {intro && <p className="mt-1 max-w-2xl text-sm text-midnight/70">{intro}</p>}

      <form method="get" action={basePath} className="mt-5 grid grid-cols-2 gap-2 rounded-2xl border border-silver/40 bg-white p-3 md:grid-cols-5">
        <input type="search" name="q" defaultValue={f.q} placeholder="Search model" aria-label="Search model" className={`${sel} col-span-2 md:col-span-1`} />
        {show("brand") && (
          <select name="brand" defaultValue={f.brand ?? ""} aria-label="Brand" className={sel}>
            <option value="">All brands</option>
            {brands.ok && brands.data.map((b) => <option key={b.slug} value={b.slug}>{b.name}</option>)}
          </select>
        )}
        {show("max_price") && (
          <select name="max_price" defaultValue={f.max_price ?? ""} aria-label="Max price" className={sel}>
            <option value="">Any price</option>
            {[10000, 15000, 20000, 30000, 50000].map((p) => <option key={p} value={p}>Up to {formatRupees(p * 100)}</option>)}
          </select>
        )}
        <select name="storage" defaultValue={f.storage ?? ""} aria-label="Storage" className={sel}>
          <option value="">Any storage</option>
          {[64, 128, 256, 512].map((s) => <option key={s} value={s}>{s} GB</option>)}
        </select>
        <select name="ram" defaultValue={f.ram ?? ""} aria-label="RAM" className={sel}>
          <option value="">Any RAM</option>
          {[4, 6, 8, 12].map((s) => <option key={s} value={s}>{s} GB RAM</option>)}
        </select>
        <select name="grade" defaultValue={f.grade ?? ""} aria-label="Grade" className={sel}>
          <option value="">Any grade</option>
          {["A", "B", "C"].map((g) => <option key={g} value={g}>Grade {g}</option>)}
        </select>
        <select name="min_battery" defaultValue={f.min_battery ?? ""} aria-label="Battery health" className={sel}>
          <option value="">Any battery</option>
          {[80, 85, 90].map((b) => <option key={b} value={b}>{b}%+ battery</option>)}
        </select>
        <select name="is_5g" defaultValue={f.is_5g ?? ""} aria-label="5G" className={sel}>
          <option value="">4G or 5G</option>
          <option value="true">5G only</option>
        </select>
        <select name="store" defaultValue={f.store ?? ""} aria-label="Store" className={sel}>
          <option value="">Any store</option>
          {stores.ok && stores.data.map((s) => <option key={s.slug} value={s.slug}>{s.name}</option>)}
        </select>
        <select name="sort" defaultValue={f.sort ?? "newest"} aria-label="Sort" className={sel}>
          <option value="newest">Newest listed</option>
          <option value="price_asc">Price: low to high</option>
          <option value="price_desc">Price: high to low</option>
          <option value="battery">Battery health</option>
        </select>
        <div className="col-span-2 flex gap-2 md:col-span-1">
          <button type="submit" className="h-10 flex-1 rounded-full bg-brand px-4 text-sm font-medium text-white hover:bg-brand-dark">
            Apply
          </button>
          <Link href={basePath} className="inline-flex h-10 items-center rounded-full border border-silver px-4 text-sm">
            Reset
          </Link>
        </div>
      </form>

      <div className="mt-6">
        {!res.ok ? (
          <p className="text-sm text-midnight/70">{res.error}</p>
        ) : res.data.items.length === 0 ? (
          <div className="rounded-2xl border border-silver/40 bg-white p-8 text-center">
            <p className="font-display font-semibold">No phones match these filters.</p>
            <p className="mt-1 text-sm text-midnight/70">Try removing a filter, or ask us on the contact page.</p>
          </div>
        ) : (
          <>
            <p className="mb-3 text-sm text-midnight/70" aria-live="polite">{res.data.total} phone{res.data.total === 1 ? "" : "s"} available</p>
            <UnitGrid units={res.data.items} />
            {res.data.total_pages > 1 && (
              <nav aria-label="Pagination" className="mt-8 flex items-center justify-center gap-3 text-sm">
                {page > 1 && <Link rel="prev" href={link(page - 1)} className="rounded-full border border-silver px-4 py-2">← Previous</Link>}
                <span className="text-midnight/70">Page {page} of {res.data.total_pages}</span>
                {page < res.data.total_pages && <Link rel="next" href={link(page + 1)} className="rounded-full border border-silver px-4 py-2">Next →</Link>}
              </nav>
            )}
          </>
        )}
      </div>
    </Container>
  );
}
