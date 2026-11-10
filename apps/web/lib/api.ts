import { apiBaseUrl } from "./config";

export type Brand = { slug: string; name: string };
export type StoreRef = { slug: string; name: string; city: string };
export type Unit = {
  unit_id: number;
  model: { slug: string; name: string; brand: Brand; is_5g: boolean };
  storage_gb: number;
  ram_gb: number | null;
  color: string | null;
  grade: "A" | "B" | "C" | null;
  battery_health: number | null;
  price_paise: number;
  store: StoreRef | null;
  photos: string[];
};
export type ModelStock = {
  slug: string;
  name: string;
  brand: Brand;
  release_year: number | null;
  is_5g: boolean;
  units_available: number;
  from_price_paise: number;
};
export type Store = { slug: string; name: string; city: string; is_demo: boolean; units_available: number };
export type Page<T> = { items: T[]; page: number; page_size: number; total: number; total_pages: number };

export type Fetched<T> = { ok: true; data: T } | { ok: false; error: string };

/** Server-side GET against the public API with a timeout (free hosting can be asleep). */
export async function apiGet<T>(path: string, timeoutMs = 20000): Promise<Fetched<T>> {
  const base = apiBaseUrl();
  if (!base) return { ok: false, error: "API URL is not configured." };
  try {
    const res = await fetch(`${base}${path}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (res.status === 404) return { ok: false, error: "not_found" };
    if (!res.ok) return { ok: false, error: `API returned ${res.status}.` };
    return { ok: true, data: (await res.json()) as T };
  } catch {
    return { ok: false, error: "We could not load live stock just now. Please try again in a minute." };
  }
}

export function qs(params: Record<string, string | number | boolean | undefined | null>): string {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") p.set(k, String(v));
  }
  const s = p.toString();
  return s ? `?${s}` : "";
}

export const getUnits = (params: Record<string, string | number | boolean | undefined>) =>
  apiGet<Page<Unit>>(`/public/units${qs(params)}`);
export const getModels = (params: Record<string, string | number | undefined> = {}) =>
  apiGet<ModelStock[]>(`/public/models${qs(params)}`);
export const getBrands = () => apiGet<Brand[]>("/public/brands");
export const getStores = () => apiGet<Store[]>("/public/stores");

export type ModelDetail = {
  slug: string;
  name: string;
  brand: Brand;
  release_year: number | null;
  is_5g: boolean;
  description: string;
  variants: { sku: string; storage_gb: number; ram_gb: number | null; color: string | null }[];
  specifications: { key: string; value: string }[];
  images: { url: string; alt: string }[];
};
export const getModel = (slug: string) => apiGet<ModelDetail>(`/catalog/models/${encodeURIComponent(slug)}`);
