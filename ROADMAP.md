# Refurbi Build Roadmap

Each task is sized for roughly one autonomous build session (~45 min). Take the first unchecked task whose dependencies are done, finish it with tests, tick it, log it in PROGRESS.md.

Legend: [ ] todo - [x] done - [!] blocked (reason in PROGRESS.md)

## Milestone 0 - Foundation
- [x] T01 Monorepo skeleton: apps/web (Next.js 15, TypeScript, Tailwind, App Router), services/api (FastAPI, Python 3.12, uv), docker-compose.yml (Postgres 16), root README run instructions
- [!] T02 CI: GitHub Actions running API lint (ruff) + tests (pytest against Postgres service) and web lint + typecheck + build
- [ ] T03 API core: settings (pydantic-settings), DB session, Alembic setup, health endpoint, consistent error envelope, pagination helper, structured logging
- [ ] T04 Design system in web: tokens (Midnight #111318, Porcelain #F7F7F5, Silver #A8B1B9, Refurbi Green #247C65), Inter + Manrope fonts, Button, Input, Select, Card, Badge (grade), Price (tabular, Rs formatting from paise), layout shells for store/admin/partner
- [ ] T05 Auth: users, roles, permissions, user_roles (counter-scoped); Argon2id; JWT access + rotating refresh (HttpOnly cookie); require_permission() dependency; seed super admin from env; tests incl. counter isolation

## Milestone 1 - Inventory core (most important)
- [ ] T06 Catalogue schema + API: brands, product_models, product_variants, specifications, images; admin CRUD; public read endpoints; seed 15 popular models (iPhone 11-15, Galaxy S21-S23, A-series, OnePlus 9-11)
- [ ] T07 Device schema: devices (imei_encrypted, imei_hash unique, grade, battery_health, cost_paise, price_paise, status, location), device_tests (JSONB checklist), device_photos, stock_movements, audit_log; partial unique indexes per D2
- [ ] T08 Device lifecycle state machine service (D7) with exhaustive transition tests; every transition writes stock_movement + audit_log
- [ ] T09 Suppliers + purchase orders + goods receipts; receiving a device requires IMEI + IMEI-check record (fake CEIR adapter in dev)
- [ ] T10 QC workflow: checklist template per category, battery %, grade assignment, photo upload (S3-compatible adapter, local disk in dev), certificate data
- [ ] T11 Pricing: landed cost (purchase + repair + logistics), suggested price by grade/margin target, manual override with audit
- [ ] T12 Admin UI: inventory table (filters brand, model, status, grade, battery, location, age), device detail page with timeline, add-device + QC screens
- [ ] T13 Stock ageing + alerts job (21-day / 35-day, QC fail, counter mismatch) on admin dashboard

## Milestone 2 - Counters & POS
- [ ] T14 Counters: schema, admin CRUD, agreements, commission rules (per model, flat/percent), verified flag gating public page
- [ ] T15 Stock transfers warehouse <-> counter with approval + IN_TRANSIT + receive confirmation
- [ ] T16 Invoice engine: GST margin scheme (Rule 32(5)) + standard mode, HSN, CGST/SGST vs IGST, FY gap-free numbering, PDF invoice; unit tests with worked examples
- [ ] T17 Partner POS UI (mobile-first): search own counter stock, sell device (customer phone + name), payment mode (cash/UPI/card recorded), issue invoice + warranty, WhatsApp-share link
- [ ] T18 Warranty: auto-created on sale, public lookup by phone + invoice no., claims workflow in admin
- [ ] T19 Commission entries per sold device + counter settlement statement
- [ ] T20 Admin dashboard: today's sales, units, gross margin, stock by location, ageing, counter leaderboard

## Milestone 3 - Public storefront
- [ ] T21 Homepage per blueprint order (product as hero, restrained motion), header/search, footer, mobile bottom nav
- [ ] T22 Listing pages /refurbished-mobiles, /refurbished-mobiles/[brand], /refurbished-mobiles/under-[price] with filters (brand, price, storage, RAM, grade, battery, 5G, store) - SSR, crawlable pagination
- [ ] T23 Product page /refurbished-[model-slug]: variant info + list of actual available units (grade, battery %, photos, price, store), specs, warranty, FAQs, sticky CTA (WhatsApp / reserve / visit store)
- [ ] T24 Reserve-for-store-pickup: phone OTP, device RESERVED 24h, notify counter; expiry job releases it
- [ ] T25 Store locator /stores + /stores/[slug] with live stock, map adapter, hours, call/WhatsApp
- [ ] T26 Exchange enquiry /exchange: questionnaire -> indicative range (rule table) -> lead saved; admin lead inbox
- [ ] T27 Trust pages: quality-check, grading, warranty, returns, about, contact, FAQ (MDX)
- [ ] T28 SEO: metadata, canonical, JSON-LD (Organization, WebSite, Product+Offer itemCondition=Refurbished, BreadcrumbList, LocalBusiness), sitemap.xml, robots.txt, redirects table

## Milestone 4 - Online payments (Release 1.5)
- [ ] T29 Cart + checkout with device reservation (row lock, 15-min hold), address, PIN-code delivery estimate stub
- [ ] T30 Payment adapter (Razorpay) with signed idempotent webhook (payment_events unique event_id); fake gateway in dev
- [ ] T31 Orders, order status history, shipments adapter, customer account (orders, warranties)
- [ ] T32 Returns/refunds workflow

## Milestone 5 - Launch hardening
- [ ] T33 Playwright E2E: POS sale, reserve-for-pickup, online purchase (fake gateway), warranty lookup
- [ ] T34 Security pass: rate limits, CORS, headers, upload validation, IMEI encryption key rotation doc, OWASP checklist
- [ ] T35 Analytics events (GA4 ecommerce + WhatsApp clicks) behind consent; Core Web Vitals check
- [ ] T36 Deployment: API Dockerfile, Vercel config, env templates, migration-on-deploy, backup/restore runbook, LAUNCH_CHECKLIST.md listing every remaining founder-provided item
