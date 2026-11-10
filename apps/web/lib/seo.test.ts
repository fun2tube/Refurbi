import { describe, expect, it } from "vitest";
import { PAGES } from "./content";
import { REDIRECTS, breadcrumbLd, ldJson, organizationLd, websiteLd } from "./seo";

describe("seo helpers", () => {
  it("builds breadcrumb positions and absolute urls", () => {
    const ld = breadcrumbLd([{ name: "Home", path: "/" }, { name: "Phones", path: "/refurbished-mobiles" }], "https://x.in");
    expect(ld.itemListElement.map((i) => i.position)).toEqual([1, 2]);
    expect(ld.itemListElement[1].item).toBe("https://x.in/refurbished-mobiles");
  });
  it("escapes < in embedded json", () => {
    expect(ldJson({ a: "</script><b>" })).not.toContain("</script>");
  });
  it("organization carries no invented facts", () => {
    expect(Object.keys(organizationLd("https://x.in")).sort()).toEqual(["@context", "@type", "name", "url"]);
    expect(websiteLd("https://x.in").potentialAction.target).toContain("{search_term_string}");
  });
  it("redirect table points at real pages and has no loops", () => {
    const real = new Set(["/refurbished-mobiles", "/stores", ...PAGES.map((p) => `/${p.slug}`)]);
    const sources = new Set(REDIRECTS.map((r) => r.source));
    for (const r of REDIRECTS) {
      expect(real.has(r.destination)).toBe(true);
      expect(sources.has(r.destination)).toBe(false);
    }
  });
});
