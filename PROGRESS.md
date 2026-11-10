# Refurbi - Build Progress

## Status
- Tasks done: 29 / 38 (76%)
- Current milestone: 4 - Online payments (Builder A next: T30)
- Next task (Builder B): none (all B tasks done)
- Preview URL: https://refurbi-web.onrender.com
- Blockers: T02 (push lacks `workflow` scope)

## Founder inputs needed (not blocking yet)
- Preview is live at https://refurbi-web.onrender.com; after the TP1-fix push, re-sync the Blueprint in Render (Blueprints > refurbi-preview > Manual sync) if it still shows the failed CORS_ORIGINS step
- Set real JWT_SECRET, SUPER_ADMIN_EMAIL/PASSWORD in the deploy env, then run `python -m app.seed` (T05)
- GSTIN, legal name, registered address (T16 invoices)
- CA sign-off on GST margin scheme (Rule 32(5)) and ITC policy
- Product photos/descriptions/spec text for the catalogue (T06 seeds only model names, years, 5G flag, RAM/storage configs - please verify; no prices/images invented)
- Grade definitions A/B/C and warranty months per grade; return window/policy; company details and contact numbers for /about, /contact, /warranty, /returns (currently marked 'to be confirmed')
- Counter list: names, addresses, owners, commission terms
- Later: domain, hosting, Razorpay, WhatsApp Business, SMS DLT, Google Maps accounts

## Log

(Older entries T01-T28 archived in docs/PROGRESS_ARCHIVE.md)

### 2026-11-10T15:30Z - T09 Suppliers, POs, goods receipts (Builder B)
- Done: D11 zero-cost decision added; app/procurement (suppliers, POs, receive with IMEI + fake CEIR adapter -> IMEI_CHECKED/BLACKLISTED via lifecycle), migration 0006, demo suppliers + PO in preview seed. API only (admin UI comes with T12).
- Tests: API 281 passed; ruff clean.
- Decisions made: receipts create device PURCHASED then lifecycle transition; fake checker blocks IMEIs starting 13579.
- Next: T10

### 2026-11-10T15:50Z - T10 QC workflow (Builder B)
- Done: app/qc: smartphone checklist template, submit QC (grade, battery %, pass/fail via lifecycle, retests), photo upload (raw body, magic-byte + 5MB validation) via storage adapter (local disk dev; R2 S3-compatible SigV4 adapter, env S3_*), certificate data endpoint, /media serving. API only (UI in T12).
- Tests: API 289 passed; ruff clean.
- Decisions made: one template for all categories (catalogue has no category yet); critical items must pass.
- Founder inputs: R2 bucket + keys at go-live (docs/GO_LIVE_FREE.md in T36); final grade definitions.
- Next: T11

### 2026-11-10T15:25Z - T11 Pricing (Builder B)
- Done: app/pricing: landed cost (purchase + repair/logistics entries), suggested price by grade margin (bps, round up to Rs 50), rules editable, apply-suggested, manual override with reason + below-cost confirmation, all audited. Migration 0007.
- Tests: API 294 passed; ruff clean (worked examples in test_pricing).
- Founder inputs: real margin targets per grade (defaults A25%/B20%/C15% are placeholders).
- Next: T12

### 2026-11-10T15:35Z - T12 Admin UI inventory/QC/receive (Builder B)
- Done: API GET /admin/inventory/devices (filters: brand, model, status, grade, battery, location, age, IMEI last4) + device detail with timeline (IMEI last4 only). Web: /admin nav, /admin/inventory table, /admin/inventory/[id] (timeline, QC form, pricing, photo upload), /admin/receive (suppliers, PO, receive with IMEI). Linked from start-page preview map.
- Tests: API 297 passed; web lint, tsc, vitest 22, build pass.
- Decisions made: token in sessionStorage (same as login); PO creation UI deferred (API only).
- Next: T13

### 2026-11-10T15:40Z - T13 Stock ageing + alerts (Builder B)
- Done: compute_alerts (AGEING 21/35d, QC_FAILED, TRANSIT_STUCK >3d, COUNTER_MISMATCH), GET /admin/inventory/alerts, alerts card on /admin dashboard. Computed on demand (no job table).
- Tests: API 299 passed; web lint/tsc/build pass.
- Next: T14

### 2026-11-10T15:50Z - T14 Counters (Builder B)
- Done: counters extended (address, owner, phone, active, verified), agreements, commission rules (FLAT paise / PERCENT bps, per-model overrides default, commission_for helper), admin CRUD under /admin/counters (new permission counters.manage), verify requires an in-force agreement. Public storefront now hides unverified/inactive counters and their stock; demo counters seeded as verified. Migration 0008.
- Tests: API 305 passed; ruff clean.
- Founder inputs: real counter list, owners, agreements and commission terms (all current counters are demo).
- Next: T15

### 2026-11-10T16:10Z - T26 Exchange enquiry (Builder A)
- Done: /exchange questionnaire -> indicative range -> lead saved; public POST /public/exchange/{quote,leads} (rate-limited, response has no PII); admin inbox /admin/exchange (new perm leads.manage, migration 0009).
- Tests: API 309 passed, ruff clean; web lint/tsc/vitest/build pass.
- Founder inputs: real exchange rule table (current values are DEMO placeholders in app/exchange/rules.py).
- Next: T24 (needs email OTP; Brevo adapter + fake)

### 2026-11-10T16:30Z - T15 Stock transfers (Builder B)
- Done: /admin/transfers create/approve/reject/cancel/receive (partial receive ok); approve -> IN_TRANSIT, receive -> AVAILABLE at destination via lifecycle service; perms transfers.manage (admin) + transfers.receive (partner, own counter only); migration 0010.
- Tests: API 313 passed; ruff clean; alembic up/down ok.
- Next: T16

### 2026-11-10T16:50Z - T16 Invoice engine (Builder B)
- Done: app/billing: GST margin scheme (Rule 32(5)) + standard mode (CGST/SGST vs IGST, integer paise), FY gap-free numbering (row-locked, rollback-safe), reportlab PDF, issue_invoice() service for T17, /admin/invoices list/detail/pdf (no cost/margin exposed); migration 0011; seller details from env (placeholders).
- Tests: API 320 passed; ruff clean; alembic up/down ok.
- Founder inputs: SELLER_GSTIN, SELLER_LEGAL_NAME, SELLER_ADDRESS, SELLER_STATE_CODE, INVOICE_PREFIX, GST_RATE_BPS (CA to confirm 18% + margin scheme eligibility) - all placeholders now.
- Next: T17

### 2026-11-10T17:10Z - T17A POS API (Builder B)
- Done: /pos/counters/{id}/stock|sales|invoices/{id}/pdf, counter-scoped (partner sees only own counter; no IMEI/cost); sale = lifecycle SOLD + invoice + Sale row; payment CASH/UPI/CARD recorded manually; UPI deep link from UPI_ID env, wa.me share link; migration 0012.
- Tests: API 323 passed; ruff clean; alembic up/down ok.
- Founder inputs: UPI_ID / UPI_PAYEE_NAME (placeholder demo@upi now).
- Next: T17B (web UI)

### 2026-11-10T17:40Z - T17B Partner POS UI (Builder B)
- Done: /partner mobile-first POS (search counter stock, sell, cash/UPI/card, invoice PDF, WhatsApp share); preview seeds partner@demo.refurbi (password = demo admin password in Render env) scoped to first demo counter; linked from start page.
- Tests: API 324 passed; web lint/tsc/vitest/build pass.
- Next: T18

### 2026-11-10T17:55Z - T18 Warranty (Builder B)
- Done: warranty auto-created on POS sale (WARRANTY_MONTHS env, default 6 = placeholder); public POST /public/warranty/lookup (phone + invoice no., rate-limited, no PII/IMEI, uniform 404); admin claims workflow (OPEN>IN_REVIEW>APPROVED/REJECTED>RESOLVED, approve -> WARRANTY_HOLD via lifecycle); UI /admin/warranty and /warranty-check; migration 0013.
- Tests: API 329 passed; ruff clean; web lint/tsc/build pass; alembic up/down ok.
- Founder inputs: warranty months per grade/terms (placeholder 6 months for all).
- Note: T15 transfers have API only (no admin UI yet) - add UI when convenient.
- Next: T19

### 2026-11-10T18:15Z - T19 Commission + settlement (Builder B)
- Done: commission entry frozen per POS sale (counter rules), counter statement (partner own via /pos/counters/{id}/commission, admin via /admin/commissions), settle -> SETTLED; UI /admin/commissions; demo 5% commission rule seeded on demo counters; migration 0014.
- Tests: API 331 passed; ruff clean; web lint/tsc/build pass; alembic up/down ok.
- Founder inputs: real commission terms; confirm who collects customer payment (assumed counter; owes sales minus commission).
- Next: T20

### 2026-11-10T21:00Z - T24 Reserve for store pickup (Builder A)
- Done: email OTP (Brevo adapter; fake outbox in dev, demo_code shown only with fake adapter outside prod) -> 24h RESERVED via lifecycle; reservations table (email PII admin-only); expiry release (lazy + POST /admin/reservations/expire for a cron); admin list/cancel; "Reserve for store pickup" on product units; migration 0015.
- Tests: API 335 passed; ruff clean; web lint/tsc/vitest/build pass; alembic up/down ok.
- Decisions: phone OTP replaced by email OTP (D11). Counter notified via email adapter is TODO (no counter email field yet). Rate limits in-memory (T34).
- Founder inputs: BREVO_API_KEY + EMAIL_FROM; a free cron (e.g. cron-job.org) hitting expiry endpoint.
- Next: T29


### 2026-11-10T16:40Z - T20 Admin dashboard (Builder B)
- Done: GET /admin/dashboard (today/month sales, units, gross margin = price - device cost, stock by location, ageing buckets, counter leaderboard; "today" = IST day) + DashboardCard on /admin.
- Tests: API 337 passed; web tsc/build ok. Pre-existing ruff E501 in migrations/0015_reservations.py (Builder A's) - not touched.
- Next: T36

### 2026-11-10T17:00Z - T36 Zero-cost deployment (Builder B)
- Done: docs/GO_LIVE_FREE.md (Neon, Render API, UptimeRobot, Cloudflare Workers, R2, Brevo, backups); OpenNext open-next.config.ts + wrangler.jsonc + cf:build/cf:deploy scripts (Render config unchanged); Neon-ready pool settings; scripts/backup.sh (pg_dump).
- Tests: API 338 passed. Cloudflare build itself not run here (needs account/network); Render fallback intact.
- Founder inputs needed: follow docs/GO_LIVE_FREE.md; GSTIN/legal name/address/UPI ID env values; confirm UptimeRobot free-plan terms are acceptable for commercial use.
- Next: none (Builder B queue empty)

### 2026-11-10T17:45Z - T29 Cart + checkout hold (Builder A)
- Done: app/checkout (checkouts/items, migration 0016): public cart check, delivery-estimate stub, checkout hold (row lock, email OTP, 15-min hold, expiry release, cancel via lifecycle). Web: /cart (localStorage cart, address, PIN estimate, countdown), Add to cart on phone page, header cart link. Fixed main web build (open-next.config.ts excluded from tsc).
- Tests: API 341 passed; ruff clean; web 24 passed, lint/typecheck/build green.
- Decisions made: payment not wired yet (T30); hold UI says nothing charged.
- Next: T30
