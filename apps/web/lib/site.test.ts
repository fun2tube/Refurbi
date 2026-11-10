import { describe, expect, it } from "vitest";
import { hasRealWhatsapp, siteUrl, whatsappLink } from "./site";

describe("site helpers", () => {
  it("builds a wa.me link with encoded text", () => {
    const l = whatsappLink("Hi, iPhone 13?", { NEXT_PUBLIC_WHATSAPP_NUMBER: "+91 98765 43210" });
    expect(l).toBe("https://wa.me/919876543210?text=Hi%2C%20iPhone%2013%3F");
  });
  it("falls back when the number is a placeholder/missing", () => {
    expect(hasRealWhatsapp({})).toBe(false);
    expect(whatsappLink("x", {})).toBe("https://wa.me/?text=x");
  });
  it("normalises the site url", () => {
    expect(siteUrl({ NEXT_PUBLIC_SITE_URL: "shop.example.in/" })).toBe("https://shop.example.in");
    expect(siteUrl({})).toMatch(/^https:\/\//);
  });
});
