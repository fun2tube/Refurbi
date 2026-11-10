import { describe, expect, it } from "vitest";
import { formatRupees } from "./money";

describe("formatRupees", () => {
  it("formats paise with Indian grouping", () => {
    expect(formatRupees(0)).toBe("₹0");
    expect(formatRupees(99900)).toBe("₹999");
    expect(formatRupees(1299900)).toBe("₹12,999");
    expect(formatRupees(12345600)).toBe("₹1,23,456");
    expect(formatRupees(1234567800)).toBe("₹1,23,45,678");
  });
  it("shows paise only when present", () => {
    expect(formatRupees(150050)).toBe("₹1,500.50");
    expect(formatRupees(5)).toBe("₹0.05");
  });
  it("handles negatives and rejects non-integers", () => {
    expect(formatRupees(-250000)).toBe("-₹2,500");
    expect(() => formatRupees(10.5)).toThrow();
  });
});
