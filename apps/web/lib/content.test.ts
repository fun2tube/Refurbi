import { describe, expect, it } from "vitest";
import { PAGES, bySlug } from "./content";

describe("trust content", () => {
  it("has the required pages with unique slugs", () => {
    const slugs = PAGES.map((p) => p.slug);
    for (const s of ["quality-check", "grading", "warranty", "returns", "about", "contact", "faq"]) expect(slugs).toContain(s);
    expect(new Set(slugs).size).toBe(slugs.length);
    expect(bySlug("nope")).toBeUndefined();
  });
  it("contains no forbidden claims", () => {
    const text = JSON.stringify(PAGES).toLowerCase();
    for (const bad of ["apple certified", "100% original", "genuine parts", "lifetime"]) expect(text).not.toContain(bad);
  });
});
