import { expect, it } from "vitest";
import { GET } from "./route";

it("health responds ok without touching the API", async () => {
  const res = GET();
  expect(res.status).toBe(200);
  expect(await res.json()).toEqual({ ok: true, service: "web" });
});
