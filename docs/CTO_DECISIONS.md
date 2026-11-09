# Refurbi - CTO Decision Record

Date: 2026-11-09 - Status: Accepted. This file overrides the original blueprint where they differ. Any build agent must treat it as authoritative.

## 1. Research findings
- India refurbished phone volumes grew ~13% YoY in H1 2026 while new-phone volumes fell ~11% (Counterpoint). Speed to a working operation matters more than polish.
- Organised channel is only ~20% of the market. The winning promise is TRUST: grading, battery health, warranty, invoice. Every screen should prove trust.
- Demand is moving upmarket (iPhones, Rs45k+ devices growing fastest). Per-device data (battery %, cosmetic photos, test report) is the conversion lever. Lead with Apple + Samsung flagships.
- Competitors: Cashify (franchise + online), Grest (Reliance Digital/Croma), ControlZ, Budli. Win locally (Mathura and nearby) with counters + WhatsApp + transparent per-unit pages.
- Indicative refurbished gross margin 15-25%. Landed cost per device and stock ageing decide profitability. Inventory system > website.
- GST Rule 32(5) margin scheme: a used-goods dealer taking no input tax credit pays GST only on (sale price - purchase price); negative margin = nil. Invoicing must support this from day one (needs per-device purchase price + ITC flag). Founder to confirm with CA.
- DoT IMEI rules: used-phone dealers are expected to verify devices against the national IMEI database (CEIR/Sanchar Saathi) before buying/selling. Mandatory IMEI verification step at goods receipt and buyback; a device cannot become AVAILABLE without a recorded check.
- Online returns are far higher than offline; counter sales come before online checkout.

## 2. Decisions
D1 Build order: operations first. Release 1 = device-level inventory + QC + IMEI check + pricing (admin); counter POS (sell, GST invoice, warranty in <2 min); public storefront showing REAL stock per counter with WhatsApp / visit store / reserve. Online payment checkout = Release 1.5.
D2 PostgreSQL 16 instead of MySQL: partial unique indexes (one active reservation/sale per device), CHECK constraints/enums for lifecycle, JSONB for QC checklists and exchange answers, cheap managed hosting.
D3 One Next.js app with route groups: /(store) public (SSR/ISR for SEO), /admin back-office, /partner counter POS. Same design system and auth. Authorisation enforced in the API, never only in UI.
D4 Modular monolith API: FastAPI + SQLAlchemy 2 + Alembic + Pydantic v2, modules catalog, inventory, procurement, counters, sales, warranty, exchange, cms. No microservices, no Celery at launch (FastAPI background tasks / DB job table). Redis optional cache only.
D5 product_variant = sellable configuration (iPhone 13/128GB/Midnight). device = one physical handset with own IMEI, grade, battery %, photos, cost, price. Public pages show the variant and list actual available units. Public APIs never expose IMEI, purchase cost, supplier, commission.
D6 Money as integer paise (BIGINT). Invoice line modes MARGIN_SCHEME (Rule 32(5), default for used phones) and STANDARD. HSN 8517. CGST/SGST vs IGST by state. Per-FY gap-free invoice numbering per GSTIN.
D7 Lifecycle: PURCHASED -> IMEI_CHECKED -> QC_PENDING -> QC_PASSED -> AVAILABLE -> RESERVED -> SOLD, plus QC_FAILED, BLACKLISTED, IN_TRANSIT, RETURNED, WARRANTY_HOLD, REPAIR, WRITTEN_OFF. One state-machine service; every transition writes stock_movements + audit_log.
D8 Auth: customers phone OTP; staff/partners email+password (Argon2id). Short-lived access JWT + rotating refresh token in HttpOnly cookie. Roles scoped by counter.
D9 Hosting: web on Vercel, API container on Railway/Render/Fly, managed Postgres with daily backups, images on Cloudflare R2. Integrations (Razorpay, WhatsApp, SMS/OTP, Maps, courier, CEIR, storage) behind adapters with FAKE implementations in dev so the build never blocks on keys.
D10 Not in Release 1: financing/EMI, AI recommendations, supplier self-service, automated commission payouts, blog CMS editor (MDX first), native apps.

## 3. Founder-only inputs
GSTIN/legal name/address; CA sign-off on margin scheme; grade definitions and warranty months per grade; counter addresses/owners/commission terms; accounts and keys (domain, Razorpay, WhatsApp Business, SMS DLT, Google Maps, hosting); product photo policy.
