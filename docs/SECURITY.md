# Security notes (T34)

## What is in place
- **Headers**: API (`app/core/security.py`) and web (`next.config.ts`) send nosniff, frame deny, referrer/permissions policy, HSTS (API: not in dev/test). API responses for `/auth`, `/admin`, `/pos`, `/partner` are `Cache-Control: no-store`.
- **CSP**: not enabled yet - Razorpay Checkout, OpenStreetMap tiles and GA4 need a tuned allowlist. Do this with the real domain at launch (start with `Content-Security-Policy-Report-Only`).
- **CORS**: explicit origin list (`CORS_ORIGINS`), no wildcard with credentials; methods/headers restricted.
- **Rate limits** (in-memory per process): login (20 failures / 10 min per IP and per email; successes are not counted), email OTP, warranty lookup, exchange quote, checkout. Move to a shared store if the API ever runs on more than one instance.
- **Uploads**: QC photos are size-capped (5 MB), magic-byte checked (JPEG/PNG/WebP only), max count per device, stored via the storage adapter.
- **Secrets**: only in env; `.env.example` has placeholders. Payment webhooks are signature-verified and idempotent.
- **PII/IMEI**: IMEI encrypted (Fernet, rotatable) + keyed hash; public endpoints are tested to never return IMEI, cost, supplier, commission or PII.
- **Auth**: Argon2id, 15-min access JWT, rotating refresh cookie (HttpOnly, SameSite=Strict), reuse revokes the family, permission checks scoped per counter.

## IMEI encryption key rotation
1. Generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
2. Set `IMEI_ENCRYPTION_KEYS=<new>,<old>` (newest first) and redeploy. Old data still decrypts.
3. `cd services/api && uv run python -m scripts.rotate_imei_keys --dry-run`, then without `--dry-run`.
4. After it reports all rows re-encrypted, remove `<old>` from the env and redeploy.
`IMEI_HASH_KEY` must NOT be rotated casually: it keys the lookup hash; changing it needs a re-hash migration (needs the plaintext, so run it in the same script pass).

## OWASP Top 10 (2021) checklist
| # | Risk | Status |
|---|------|--------|
| A01 | Broken access control | Permission dependency on every admin/POS/partner route; counter scoping tested |
| A02 | Cryptographic failures | Argon2id, Fernet IMEI, HSTS; secrets from env |
| A03 | Injection | SQLAlchemy parameterised queries; pydantic validation; React escapes output |
| A04 | Insecure design | Reservations/holds server-side with row locks; webhooks idempotent |
| A05 | Misconfiguration | Security headers; CORS allowlist; demo OTP echo only for dev/preview/test + fake email |
| A06 | Vulnerable components | `npm audit` / `uv` lock files; run before launch (founder task: enable Dependabot) |
| A07 | Identification/auth failures | Login throttle, refresh rotation, OTP lockout |
| A08 | Integrity failures | Signed payment webhooks; no unsigned deserialisation |
| A09 | Logging/monitoring | Structured request logs with request id; no secrets/PII in logs (review at launch) |
| A10 | SSRF | No user-supplied URLs fetched by the server |
Open items for launch: CSP, shared rate-limit store if scaled out, Dependabot, pen-test of payment flow with real Razorpay test keys.
