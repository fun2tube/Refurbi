import { describe, expect, it } from "vitest";
import { mapFor } from "./maps";

describe("map adapter", () => {
  it("returns a placeholder by default", () => {
    expect(mapFor({ name: "A", city: "B" }, undefined).kind).toBe("placeholder");
  });
  it("builds an encoded maps link for google-link", () => {
    const v = mapFor({ name: "Demo Counter A", city: "Demo City" }, "google-link");
    expect(v.kind).toBe("link");
    if (v.kind === "link") expect(v.href).toContain("Demo%20Counter%20A%20Demo%20City");
  });
});
