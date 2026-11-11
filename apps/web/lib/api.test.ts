import { beforeEach, describe, expect, it, vi } from "vitest";
import { _clearCache, _deps, apiGet, WAKING_MESSAGE } from "./api";

const json = (status: number, body: unknown = {}) => new Response(JSON.stringify(body), { status });

describe("apiGet", () => {
  let t = 0;
  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_URL = "https://api.test";
    t = 0;
    _clearCache();
    _deps.now = () => t;
    _deps.sleep = async (ms) => {
      t += ms;
    };
  });

  it("retries 502 with backoff then succeeds", async () => {
    const f = vi.fn().mockResolvedValueOnce(json(502)).mockResolvedValueOnce(json(502)).mockResolvedValueOnce(json(200, { a: 1 }));
    _deps.fetch = f;
    expect(await apiGet("/x")).toEqual({ ok: true, data: { a: 1 } });
    expect(f).toHaveBeenCalledTimes(3);
    expect(t).toBe(3000);
  });

  it("returns a friendly waking state after the budget, not a raw 502", async () => {
    _deps.fetch = vi.fn().mockResolvedValue(json(502));
    const r = await apiGet("/x");
    expect(r).toEqual({ ok: false, error: WAKING_MESSAGE, waking: true });
    expect(t).toBeLessThanOrEqual(60000);
  });

  it("does not retry 4xx or 404", async () => {
    const f = vi.fn().mockResolvedValue(json(404));
    _deps.fetch = f;
    expect(await apiGet("/x")).toEqual({ ok: false, error: "not_found" });
    expect(f).toHaveBeenCalledTimes(1);
  });

  it("retries network errors", async () => {
    const f = vi.fn().mockRejectedValueOnce(new Error("ECONNRESET")).mockResolvedValueOnce(json(200, [1]));
    _deps.fetch = f;
    expect((await apiGet("/x")).ok).toBe(true);
  });

  it("caches when asked, and serves stale if the API goes down", async () => {
    const f = vi.fn().mockResolvedValue(json(200, { v: 1 }));
    _deps.fetch = f;
    await apiGet("/c", { cache: true });
    await apiGet("/c", { cache: true });
    expect(f).toHaveBeenCalledTimes(1);
    t += 61000;
    _deps.fetch = vi.fn().mockResolvedValue(json(502));
    expect(await apiGet("/c", { cache: true })).toEqual({ ok: true, data: { v: 1 } });
  });
});
