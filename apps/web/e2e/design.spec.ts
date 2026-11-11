import { expect, test } from "@playwright/test";
import { firstModelSlug } from "./helpers";

// TP3/TP4: cinematic pages on a production build at phone width: no horizontal overflow, no console errors.
const noOverflow = (page: import("@playwright/test").Page) =>
  page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);

test("home film, listing filter sheet and product flip work at phone width", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("checked and graded");
  await expect(page.getByRole("heading", { name: /checked, cleaned and brought back/i })).toBeVisible();
  expect(await noOverflow(page)).toBe(true);

  await page.goto("/refurbished-mobiles");
  await page.getByRole("button", { name: /^Filters/ }).click();
  await expect(page.getByRole("dialog", { name: "Filters" })).toBeVisible();
  await page.getByRole("button", { name: "Close" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  expect(await noOverflow(page)).toBe(true);

  const slug = await firstModelSlug(request);
  await page.goto(`/product/${slug}`);
  const flip = page.getByRole("button", { name: "At a glance" });
  await flip.click();
  await expect(page.getByRole("button", { name: "Show phone" })).toHaveAttribute("aria-pressed", "true");
  expect(await noOverflow(page)).toBe(true);
  expect(errors).toEqual([]);
});
