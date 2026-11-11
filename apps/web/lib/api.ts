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

export type Fetched<T> = { ok: true; data: T } | { ok: false; error: string; waking?: boolean };

export const WAKING_MESSAGE = "Waking up the store. This can take up to a minute on the first visit.";

const RETRY_STATUSES = new Set([429, 502, 503, 504]);
const CACHE_TTL_MS = 60_000;
const CACHE_MAX = 100;
const cache = new Map<string, { at: number; data: unknown }>();

/** Test hooks (fetch + sleep are injectable so retries run instantly). */
export const _deps = {
  fetch: (url: string, init: RequestInit) => fetch(url, init),
  sleep: (ms: number) => new Promise<void>((r) => setTimeout(r, ms)),
  now: () => Date.now(),
};
export const _clearCache = () => cache.clear();

type GetOpts = { timeoutMs?: number; budgetMs?: number; cache?: boolean };

/** Server-side GET against the public API. Free hosting sleeps, so 502/503/504 and network errors
 *  are retried with exponential backoff within `budgetMs` (~60s). Public reads are cached in memory
 *  for 60s (and served stale if the API is down). */
export async function apiGet<T>(path: string, opts: GetOpts | number = {}): Promise<Fetched<T>> {
  const o: GetOpts = typeof opts === "number" ? { timeoutMs: opts, budgetMs: opts } : opts;
  const { timeoutMs = 15000, budgetMs = 60000, cache: useCache = false } = o;
  const base = apiBaseUrl();
  if (!base) return { ok: false, error: "API URL is not configured." };
  const hit = useCache ? cache.get(path) : undefined;
  if (hit && _deps.now() - hit.at < CACHE_TTL_MS) return { ok: true, data: hit.data as T };

  const started = _deps.now();
  let delay = 1000;
  let lastStatus = 0;
  for (;;) {
    let retry = false;
    try {
      const res = await _deps.fetch(`${base}${path}`, {
        cache: "no-store",
        signal: AbortSignal.timeout(timeoutMs),
      });
      if (res.status === 404) return { ok: false, error: "not_found" };
      if (res.ok) {
        const data = (await res.json()) as T;
        if (useCache) {
          if (cache.size >= CACHE_MAX) cache.delete(cache.keys().next().value as string);
          cache.set(path, { at: _deps.now(), data });
        }
        return { ok: true, data };
      }
      lastStatus = res.status;
      retry = RETRY_STATUSES.has(res.status);
    } catch {
      retry = true;
    }
    if (!retry) return { ok: false, error: `The store could not load this just now (error ${lastStatus}). Please try again.` };
    if (_deps.now() - started + delay > budgetMs) break;
    await _deps.sleep(delay);
    delay = Math.min(delay * 2, 8000);
  }
  if (hit) return { ok: true, data: hit.data as T }; // stale beats nothing
  return { ok: false, error: WAKING_MESSAGE, waking: true };
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
  apiGet<Page<Unit>>(`/public/units${qs(params)}`, { cache: true });
export const getModels = (params: Record<string, string | number | undefined> = {}) =>
  apiGet<ModelStock[]>(`/public/models${qs(params)}`, { cache: true });
export const getBrands = () => apiGet<Brand[]>("/public/brands", { cache: true });
export const getStores = () => apiGet<Store[]>("/public/stores", { cache: true });

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
export const getModel = (slug: string) => apiGet<ModelDetail>(`/catalog/models/${encodeURIComponent(slug)}`, { cache: true });
