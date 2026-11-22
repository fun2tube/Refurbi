import { describe, expect, it } from "vitest";
import { cheapestId, parseCompare, toCompareItem, MAX_COMPARE } from "./compare";
import type { Unit } from "./api";

const unit = (id: number, price: number): Unit => ({
  unit_id: id,
  model: { slug: "iphone-12", name: "iPhone 12", brand: { slug: "apple", name: "Apple" }, is_5g: true },
  storage_gb: 128, ram_gb: 4, color: null, grade: "A", battery_health: 90, price_paise: price, store: null, photos: [],
} as unknown as Unit);

describe("compare", () => {
  it("snapshots only public fields", () => {
    const i = toCompareItem(unit(1, 1000));
    expect(Object.keys(i).sort()).toEqual(["battery_health", "brand", "grade", "id", "name", "photo", "price_paise", "ram_gb", "slug", "storage_gb", "store"]);
  });
  it("parses defensively", () => {
    expect(parseCompare("nope")).toEqual([]);
    expect(parseCompare('{"a":1}')).toEqual([]);
    const many = JSON.stringify([1, 2, 3, 4, 2].map((n) => toCompareItem(unit(n, 5))));
    expect(parseCompare(many)).toHaveLength(MAX_COMPARE);
    expect(parseCompare('[{"id":1,"name":"x","price_paise":5,"photo":"javascript:1"}]')[0].photo).toBeNull();
  });
  it("finds cheapest only when comparing 2+", () => {
    expect(cheapestId([toCompareItem(unit(1, 9))])).toBeNull();
    expect(cheapestId([toCompareItem(unit(1, 9)), toCompareItem(unit(2, 7))])).toBe(2);
  });
});
