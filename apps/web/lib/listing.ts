export type SP = Record<string, string | string[] | undefined>;

const FILTER_KEYS = ["q", "brand", "max_price", "storage", "ram", "grade", "min_battery", "is_5g", "store", "sort"] as const;

const one = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v);

/** Whitelist + normalise query params so only known filters reach the API. */
export function cleanFilters(sp: SP): Record<string, string> {
  const out: Record<string, string> = {};
  for (const k of FILTER_KEYS) {
    const v = one(sp[k])?.trim();
    if (v) out[k] = v.slice(0, 60);
  }
  return out;
}

export function pageNumber(sp: SP): number {
  const n = Number.parseInt(one(sp.page) ?? "1", 10);
  return Number.isFinite(n) && n >= 1 ? Math.min(n, 500) : 1;
}

/** Parse /refurbished-mobiles/<slug>: `under-<rupees>` is a budget page, anything else a brand. */
export function parseListingSlug(slug: string): { kind: "budget"; rupees: number } | { kind: "brand"; slug: string } | null {
  const m = /^under-(\d{4,6})$/.exec(slug);
  if (m) {
    const rupees = Number.parseInt(m[1], 10);
    return rupees >= 1000 ? { kind: "budget", rupees } : null;
  }
  if (slug.startsWith("under-")) return null;
  return /^[a-z0-9]+(-[a-z0-9]+)*$/.test(slug) ? { kind: "brand", slug } : null;
}
