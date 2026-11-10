import { describe, expect, it } from "vitest";
import { apiBaseUrl, isPreview, normaliseBaseUrl } from "./config";

describe("normaliseBaseUrl", () => {
  it("adds https to bare hosts", () => {
    expect(normaliseBaseUrl("refurbi-api.onrender.com")).toBe("https://refurbi-api.onrender.com");
  });
  it("keeps full URLs and strips trailing slash", () => {
    expect(normaliseBaseUrl("https://a.example/")).toBe("https://a.example");
    expect(normaliseBaseUrl("http://localhost:8000")).toBe("http://localhost:8000");
  });
  it("handles empty", () => {
    expect(normaliseBaseUrl(undefined)).toBe("");
    expect(normaliseBaseUrl("  ")).toBe("");
  });
});

describe("apiBaseUrl", () => {
  it("uses env when set", () => {
    expect(apiBaseUrl({ NEXT_PUBLIC_API_URL: "api.example.com" })).toBe("https://api.example.com");
  });
  it("falls back to localhost only in development", () => {
    expect(apiBaseUrl({ NODE_ENV: "development" })).toBe("http://localhost:8000");
    expect(apiBaseUrl({ NODE_ENV: "production" })).toBe("");
  });
});

describe("isPreview", () => {
  it("is true only for APP_ENV=preview", () => {
    expect(isPreview({ APP_ENV: "preview" })).toBe(true);
    expect(isPreview({ NEXT_PUBLIC_APP_ENV: "preview" })).toBe(true);
    expect(isPreview({ APP_ENV: "dev" })).toBe(false);
    expect(isPreview({})).toBe(false);
  });
});
