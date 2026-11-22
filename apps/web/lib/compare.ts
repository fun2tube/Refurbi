/** Browser compare list: up to 3 public unit snapshots (no IMEI/cost/supplier ever stored). */
import type { Unit } from "@/lib/api";

const KEY = "refurbi.compare.v1";
export const MAX_COMPARE = 3;

export type CompareItem = {
  id: number;
  slug: string;
  name: string;
  brand: string;
  storage_gb: number;
  ram_gb: number | null;
  grade: "A" | "B" | "C" | null;
  battery_health: number | null;
  price_paise: number;
  photo: string | null;
  store: string | null;
};

export function toCompareItem(u: Unit): CompareItem {
  return {
    id: u.unit_id,
    slug: u.model.slug,
    name: `${u.model.name} ${u.storage_gb}GB`,
    brand: u.model.brand.name,
    storage_gb: u.storage_gb,
    ram_gb: u.ram_gb,
    grade: u.grade,
    battery_health: u.battery_health,
    price_paise: u.price_paise,
    photo: u.photos[0] ?? null,
    store: u.store?.name ?? null,
  };
}

export function parseCompare(raw: string | null): CompareItem[] {
  try {
    const v = JSON.parse(raw ?? "[]");
    if (!Array.isArray(v)) return [];
    const seen = new Set<number>();
    const out: CompareItem[] = [];
    for (const x of v) {
      if (!x || !Number.isInteger(x.id) || x.id <= 0 || typeof x.name !== "string" || !Number.isInteger(x.price_paise)) continue;
      if (seen.has(x.id)) continue;
      seen.add(x.id);
      out.push({
        id: x.id,
        slug: String(x.slug ?? ""),
        name: x.name,
        brand: String(x.brand ?? ""),
        storage_gb: Number(x.storage_gb) || 0,
        ram_gb: Number.isFinite(x.ram_gb) ? x.ram_gb : null,
        grade: x.grade === "A" || x.grade === "B" || x.grade === "C" ? x.grade : null,
        battery_health: Number.isFinite(x.battery_health) ? x.battery_health : null,
        price_paise: x.price_paise,
        photo: typeof x.photo === "string" && x.photo.startsWith("http") ? x.photo : null,
        store: typeof x.store === "string" ? x.store : null,
      });
    }
    return out.slice(0, MAX_COMPARE);
  } catch {
    return [];
  }
}

export function readCompare(): CompareItem[] {
  try {
    return parseCompare(localStorage.getItem(KEY));
  } catch {
    return [];
  }
}

function write(items: CompareItem[]): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(items.slice(0, MAX_COMPARE)));
  } catch {
    /* storage unavailable: compare list does not persist */
  }
  window.dispatchEvent(new Event("refurbi-compare"));
}

/** Toggle membership. Returns "full" when adding to a full list. */
export function toggleCompare(item: CompareItem): "added" | "removed" | "full" {
  const cur = readCompare();
  if (cur.some((c) => c.id === item.id)) {
    write(cur.filter((c) => c.id !== item.id));
    return "removed";
  }
  if (cur.length >= MAX_COMPARE) return "full";
  write([...cur, item]);
  return "added";
}

export const removeCompare = (id: number) => write(readCompare().filter((c) => c.id !== id));
export const clearCompare = () => write([]);

/** Index of the cheapest item (ties: first), for the "best" highlight. */
export function cheapestId(items: CompareItem[]): number | null {
  return items.length < 2 ? null : items.reduce((a, b) => (b.price_paise < a.price_paise ? b : a)).id;
}
