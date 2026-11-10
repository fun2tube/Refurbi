# E2E (Playwright)

Runs against a real API in demo mode (fake payment gateway, fake email adapter that echoes the OTP, no real keys).
`./e2e/run.sh` does everything: scratch DB, migrate, seed, API on :8000, web on :3000, then the tests.
Needs Postgres reachable via `E2E_DATABASE_URL` (default local `refurbi_e2e`), `uv`, and Playwright's Chromium.
Not in GitHub Actions yet (workflow pushes are blocked - T02); a CI job draft is in `ci/ci.yml`.
