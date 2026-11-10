import { describe, expect, it } from "vitest";
import { cleanFilters, pageNumber, parseListingSlug } from "./listing";

describe("listing helpers", () => {
  it("parses slugs", () => {
    expect(parseListingSlug("under-20000")).toEqual({ kind: "budget", rupees: 20000 });
    expect(parseListingSlug("apple")).toEqual({ kind: "brand", slug: "apple" });
    expect(parseListingSlug("Bad_Slug")).toBeNull();
    expect(parseListingSlug("under-5")).toBeNull();
  });
  it("whitelists filters and clamps page", () => {
    expect(cleanFilters({ grade: "A", evil: "x", q: " iphone " })).toEqual({ grade: "A", q: "iphone" });
    expect(pageNumber({ page: "0" })).toBe(1);
    expect(pageNumber({ page: "abc" })).toBe(1);
    expect(pageNumber({ page: "3" })).toBe(3);
  });
});
