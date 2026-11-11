import { expect, test } from "@playwright/test";
import { firstModelSlug } from "./helpers";

test("reserve a phone for store pickup (fake email OTP)", async ({ page, request }) => {
  const slug = await firstModelSlug(request);
  await page.goto(`/product/${slug}`);
  await page.getByRole("button", { name: /reserve for store pickup/i }).first().click();
  await page.getByLabel("Your name").fill("E2E Reserve");
  await page.getByLabel("Email").fill(`reserve-${Date.now()}@example.com`);
  await page.getByRole("button", { name: "Send code" }).click();
  const hint = page.getByText(/your code is \d+/);
  await expect(hint).toBeVisible();
  const code = (await hint.innerText()).match(/your code is (\d+)/)![1];
  await page.getByLabel("6-digit code").fill(code);
  await page.getByRole("button", { name: /reserve for 24 hours/i }).click();
  await expect(page.getByText(/Reserved! Your code:/)).toBeVisible();
});

test("online purchase: cart, 15-minute hold, fake gateway payment", async ({ page, request }) => {
  const slug = await firstModelSlug(request);
  await page.goto(`/product/${slug}`);
  // .last(): the reserve test above takes the first unit and the product page is served from the 60s response cache
  await page.getByRole("button", { name: "Add to cart" }).last().click();
  await page.goto("/cart");
  await page.getByLabel("Full name").fill("E2E Buyer");
  await page.getByLabel("Email").fill(`buyer-${Date.now()}@example.com`);
  await page.getByLabel("Phone", { exact: true }).fill("9876543210");
  await page.getByLabel("Address").fill("1 Demo Street");
  await page.getByLabel("City").fill("Demo City");
  await page.getByLabel("PIN code").fill("560001");
  await page.getByRole("button", { name: "Send code" }).click();
  const hint = page.getByText(/your code is \d+/);
  await expect(hint).toBeVisible();
  const code = (await hint.innerText()).match(/your code is (\d+)/)![1];
  await page.getByLabel("6-digit code").fill(code);
  await page.getByRole("button", { name: "Hold for 15 minutes" }).click();
  await page.getByRole("button", { name: /^Pay / }).click();
  await expect(page.getByText("Payment received. Thank you!")).toBeVisible();
});
