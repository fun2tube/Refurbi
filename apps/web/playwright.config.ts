import { defineConfig } from "@playwright/test";

// E2E runs against a real API (APP_ENV=preview/dev, fake gateway + fake email adapter) - see e2e/README.md.
const WEB = process.env.E2E_WEB_URL ?? "http://localhost:3000";
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  retries: 0,
  workers: 1,
  reporter: [["list"]],
  use: { baseURL: WEB, trace: "off" },
  projects: [{ name: "mobile-chromium", use: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } }],
});
