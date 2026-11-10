import { APIRequestContext, expect } from "@playwright/test";

export const API = process.env.E2E_API_URL ?? "http://localhost:8000";
const ADMIN = {
  email: process.env.E2E_ADMIN_EMAIL ?? "admin@example.com",
  password: process.env.E2E_ADMIN_PASSWORD ?? "e2e-password",
};

/** First publicly listed unit (never carries IMEI/cost) -> model slug to open its product page. */
export async function firstModelSlug(request: APIRequestContext, skipModelSlugs: string[] = []): Promise<string> {
  const r = await request.get(`${API}/public/units?limit=30`);
  expect(r.ok()).toBeTruthy();
  const items = (await r.json()).items as { model: { slug: string } }[];
  const hit = items.find((i) => !skipModelSlugs.includes(i.model.slug));
  expect(hit, "preview seed should expose available units").toBeTruthy();
  return hit!.model.slug;
}

export async function adminToken(request: APIRequestContext): Promise<string> {
  const r = await request.post(`${API}/auth/login`, { data: ADMIN });
  expect(r.ok(), "super admin login (see e2e/README.md)").toBeTruthy();
  return (await r.json()).access_token;
}
