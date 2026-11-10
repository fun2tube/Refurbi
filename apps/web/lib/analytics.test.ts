import { describe, expect, it } from "vitest";
import { cfBeaconToken, events, gaId, track, vitalsParams } from "./analytics";

describe("analytics config", () => {
  it("accepts only well-formed GA4 ids", () => {
    expect(gaId({ NEXT_PUBLIC_GA_MEASUREMENT_ID: "G-ABC123XYZ" })).toBe("G-ABC123XYZ");
    expect(gaId({ NEXT_PUBLIC_GA_MEASUREMENT_ID: "UA-1" })).toBe("");
    expect(gaId({})).toBe("");
  });
  it("accepts only hex Cloudflare beacon tokens", () => {
    expect(cfBeaconToken({ NEXT_PUBLIC_CF_BEACON_TOKEN: "0123456789abcdef0123456789abcdef" })).toBeTruthy();
    expect(cfBeaconToken({ NEXT_PUBLIC_CF_BEACON_TOKEN: "<script>" })).toBe("");
  });
  it("track is a no-op without a window / config / consent", () => {
    expect(track("add_to_cart", {})).toBe(false);
  });
});

describe("event payloads", () => {
  it("converts paise to rupees and carries only ids and values", () => {
    const p = events.purchase("tok", [{ unit_id: 7, price_paise: 1_236_000 }], 1_236_000);
    expect(p).toMatchObject({ currency: "INR", value: 12360, transaction_id: "tok" });
    expect(JSON.stringify(p)).not.toMatch(/imei|email|phone|name/i);
    expect(events.addToCart(3)).toEqual({ currency: "INR", items: [{ item_id: "3", quantity: 1 }] });
    expect(events.beginCheckout([], 0)).toMatchObject({ value: 0, items: [] });
  });
  it("rounds web vitals", () => {
    expect(vitalsParams({ name: "CLS", value: 0.12345, id: "x" }).metric_value).toBe(0.123);
    expect(vitalsParams({ name: "LCP", value: 2500.7, id: "x" }).metric_value).toBe(2501);
  });
});
