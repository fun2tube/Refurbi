# Refurbi Build Roadmap

## Priority: storefront first
Two parallel streams: Builder A = storefront (T21-T35), Builder B = back-office (T09-T20, T36). Zero-cost rule (D11): no paid services; every integration behind an adapter with a dev fake.

Founder-approved 2026-11-10: Milestone 3 (T21-T28) is done BEFORE the remaining Milestone 1/2 tasks. T21-T28 use demo data and public read-only endpoints (never exposing IMEI, cost, supplier or commission). Order: T21, T22, T23, T25, T27, T28, T26, T24, then T09, T10, T11, T12, T13, T14... in normal order.

Each task is sized for roughly one autonomous build session (~45 min). Take the first unchecked task whose dependencies are done, finish it with tests, tick it, log it in PROGRESS.md.

Legend: [ ] todo - [x] done - [!] blocked (reason in PROGRESS.md)

## Milestone 0 - Foundation
- [x] T01 Monorepo skeleton: apps/web (Next.js 15, TypeScript, Tailwind, App Router), services/api (FastAPI, Python 3.12, uv), docker-compose.yml (Postgres 16), root README run instructions
- [!] T02 CI: GitHub Actions running API lint (ruff) + tests (pytest against Postgres service) and web lint + typecheck + build
- [x] T03 API core: settings (pydantic-settings), DB session, Alembic setup, health endpoint, consistent error envelope, pagination helper, structured logging
- [x] T04 Design system in web: tokens (Midnight #111318, Porcelain #F7F7F5, Silver #A8B1B9, Refurbi Green #247C65), Inter + Manrope fonts, Button, Input, Select, Card, Badge (grade), Price (tabular, Rs formatting from paise), layout shells for store/admin/partner
- [x] T05 Auth: users, roles, permissions, user_roles (counter-scoped); Argon2id; JWT access + rotating refresh (HttpOnly cookie); require_permission() dependency; seed super admin from env; tests incl. counter isolation

## Milestone 1 - Inventory core (most important)
- [x] T06 Catalogue schema + API: brands, product_models, product_variants, specifications, images; admin CRUD; public read endpoints; seed 15 popular models (iPhone 11-15, Galaxy S21-S23, A-series, OnePlus 9-11)
- [x] T07 Device schema: devices (imei_encrypted, imei_hash unique, grade, battery_health, cost_paise, price_paise, status, location), device_tests (JSONB checklist), device_photos, stock_movements, audit_log; partial unique indexes per D2
- [x] TP1 One-click preview deployment on Render ONLY: root `render.yaml` Blueprint (free Postgres + API web service + Next.js web service, all env wired/generated, no manual env vars), idempotent demo seed (demo counters, ~30 demo devices, demo admin), 'Demo data' banner when APP_ENV=preview, preview start page at `/`, docs/PREVIEW_SETUP.md (founder-approved 2026-11-10)
- [x] T08 Device lifecycle state machine service (D7) with exhaustive transition tests; every transition writes stock_movement + audit_log
- [x] T09 Suppliers + purchase orders + goods receipts; receiving a device requires IMEI + IMEI-check record (fake CEIR adapter in dev)
- [x] T10 QC workflow: checklist template per category, battery %, grade assignment, photo upload (S3-compatible adapter, local disk in dev), certificate data
- [x] T11 Pricing: landed cost (purchase + repair + logistics), suggested price by grade/margin target, manual override with audit
- [x] T12 Admin UI: inventory table (filters brand, model, status, grade, battery, location, age), device detail page with timeline, add-device + QC screens
- [x] T13 Stock ageing + alerts job (21-day / 35-day, QC fail, counter mismatch) on admin dashboard

## Milestone 2 - Counters & POS
- [x] T14 Counters: schema, admin CRUD, agreements, commission rules (per model, flat/percent), verified flag gating public page
- [x] T15 Stock transfers warehouse <-> counter with approval + IN_TRANSIT + receive confirmation
- [x] T16 Invoice engine: GST margin scheme (Rule 32(5)) + standard mode, HSN, CGST/SGST vs IGST, FY gap-free numbering, PDF invoice; unit tests with worked examples
- [x] T17A (API) Partner POS UI (mobile-first): search own counter stock, sell device (customer phone + name), payment mode (cash/UPI/card recorded), issue invoice + warranty, WhatsApp-share link
- [x] T17B Partner POS web UI (mobile-first) on top of the T17A API, linked from start page
- [x] T18 Warranty: auto-created on sale, public lookup by phone + invoice no., claims workflow in admin
- [x] T19 Commission entries per sold device + counter settlement statement
- [x] T20 Admin dashboard: today's sales, units, gross margin, stock by location, ageing, counter leaderboard

## Milestone 3 - Public storefront
- [x] T21 Homepage per blueprint order (product as hero, restrained motion), header/search, footer, mobile bottom nav
- [x] T22 Listing pages /refurbished-mobiles, /refurbished-mobiles/[brand], /refurbished-mobiles/under-[price] with filters (brand, price, storage, RAM, grade, battery, 5G, store) - SSR, crawlable pagination
- [x] T23 Product page /refurbished-[model-slug]: variant info + list of actual available units (grade, battery %, photos, price, store), specs, warranty, FAQs, sticky CTA (WhatsApp / reserve / visit store)
- [x] T24 Reserve-for-store-pickup: phone OTP, device RESERVED 24h, notify counter; expiry job releases it
- [x] T25 Store locator /stores + /stores/[slug] with live stock, map adapter, hours, call/WhatsApp
- [x] T26 Exchange enquiry /exchange: questionnaire -> indicative range (rule table) -> lead saved; admin lead inbox
- [x] T27 Trust pages: quality-check, grading, warranty, returns, about, contact, FAQ (MDX)
- [x] T28 SEO: metadata, canonical, JSON-LD (Organization, WebSite, Product+Offer itemCondition=Refurbished, BreadcrumbList, LocalBusiness), sitemap.xml, robots.txt, redirects table

## Milestone 4 - Online payments (Release 1.5)
- [x] T29 Cart + checkout with device reservation (row lock, 15-min hold), address, PIN-code delivery estimate stub
- [x] T30 Payment adapter (Razorpay) with signed idempotent webhook (payment_events unique event_id); fake gateway in dev
- [x] T31A Orders from paid checkouts, status history, courier adapter (fake), public tracking, email-OTP "My orders" page, admin order API
- [x] T31B Admin orders UI; GST invoice + warranty for online orders; warranties in customer account (Orders, order status history, shipments adapter, customer account (orders, warranties))
- [x] T32 Returns/refunds workflow

## Milestone 5 - Launch hardening
- [x] T33 Playwright E2E: POS sale, reserve-for-pickup, online purchase (fake gateway), warranty lookup (apps/web/e2e, `npm run e2e`)
- [ ] T34 Security pass: rate limits, CORS, headers, upload validation, IMEI encryption key rotation doc, OWASP checklist
- [ ] T35 Analytics events (GA4 ecommerce + WhatsApp clicks) behind consent; Core Web Vitals check
- [x] T36 Deployment: API Dockerfile, Vercel config, env templates, migration-on-deploy, backup/restore runbook, LAUNCH_CHECKLIST.md listing every remaining founder-provided item
