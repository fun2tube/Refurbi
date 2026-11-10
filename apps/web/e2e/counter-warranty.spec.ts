import { expect, test } from "@playwright/test";
import { adminToken, API } from "./helpers";

test("POS counter sale, then public warranty lookup (phone + invoice)", async ({ page, request }) => {
  const auth = { Authorization: `Bearer ${await adminToken(request)}` };
  const stock = await request.get(`${API}/pos/counters/1/stock?counter_id=1`, { headers: auth });
  expect(stock.ok()).toBeTruthy();
  const items = (await stock.json()) as Record<string, unknown>[];
  expect(items.length).toBeGreaterThan(0);
  for (const bad of ["cost", "imei_encrypted", "supplier", "commission"]) expect(JSON.stringify(items)).not.toContain(bad);

  const phone = "9123456780";
  const sale = await request.post(`${API}/pos/counters/1/sales`, {
    headers: auth,
    data: { device_id: items[0].device_id, customer_name: "E2E Walk-in", customer_phone: phone, payment_mode: "CASH" },
  });
  expect(sale.status()).toBe(201);
  const { invoice_number } = await sale.json();
  expect(invoice_number).toMatch(/^DEMO\//);

  await page.goto("/warranty-check");
  await page.getByLabel("Mobile number").fill(phone);
  await page.getByLabel("Invoice number").fill(invoice_number);
  await page.getByRole("button", { name: "Check warranty" }).click();
  await expect(page.getByText(`Invoice ${invoice_number}`)).toBeVisible();

  await page.getByLabel("Mobile number").fill("9000000000");
  await page.getByRole("button", { name: "Check warranty" }).click();
  await expect(page.getByText("No warranty found for these details.")).toBeVisible();
});
