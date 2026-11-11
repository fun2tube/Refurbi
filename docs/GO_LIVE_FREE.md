# Go live for free (D11) - click-by-click

Everything below is free, commercial use allowed, no credit card. Estimated time: 60-90 minutes.
Items marked **[you]** need your own accounts or business facts; nothing here is invented for you.

## 1. Neon (database)
1. neon.tech > Sign up with Google/GitHub (no card).
2. Create project `refurbi`, region **Singapore** (closest to India), Postgres 16.
3. Dashboard > Connection details. Copy two strings: **Pooled** (host has `-pooler`) and **Direct**.
4. Use the **Direct** string as `DATABASE_URL` for the API (migrations need a direct connection). `postgresql://...?sslmode=require` is fine as pasted; the app rewrites it for the driver.
5. Neon free auto-suspends when idle; the first request after sleep takes ~1-3 s (the API retries/validates connections).

## 2. API on Render (free web service)
1. render.com > New > Web Service > pick this repo, Runtime **Docker**, Dockerfile path `./services/api/Dockerfile`, context `./services/api`. Plan **Free** (no card).
   (The existing `render.yaml` Blueprint also works for the preview; for production, remove the `databases:` block and set `DATABASE_URL` to the Neon Direct string.)
2. Environment variables: `APP_ENV=production`, `DATABASE_URL` (Neon), `JWT_SECRET` and `IMEI_ENCRYPTION_KEYS` and `IMEI_HASH_KEY` (each a long random string, e.g. `openssl rand -hex 32`; **keep them safe, losing the IMEI keys makes stored IMEIs unreadable**), `SUPER_ADMIN_EMAIL`, `SUPER_ADMIN_PASSWORD`, `CORS_ORIGINS` (your web URL), **[you]** `SELLER_GSTIN`, `SELLER_LEGAL_NAME`, `SELLER_ADDRESS`, `SELLER_STATE_CODE`, `UPI_ID`, `UPI_PAYEE_NAME`.
3. Deploy. The container runs migrations and the idempotent seed on start (`scripts/start.sh`). Open `https://<api>.onrender.com/health`.

## 3. UptimeRobot (keep BOTH services warm)
1. uptimerobot.com > free account (no card).
2. Add New Monitor > type **HTTP(s)**, URL `https://<api>.onrender.com/health`, interval **5 minutes** (free minimum).
3. Add a **second** monitor for the web service: `https://<web>.onrender.com/api/health` (also every 5 minutes). Both services must be pinged: a sleeping web service shows a Render error page, a sleeping API shows the in-site "Waking up" state (the site retries for up to ~60s).
4. This stops Render free from sleeping (it sleeps after 15 min idle). Free plans are for non-commercial use per UptimeRobot terms - if that matters to you, alternatives are cron-job.org (free) hitting the same URL every 10 min.

## 4. Web on Cloudflare Workers (OpenNext)
1. dash.cloudflare.com > sign up (no card). Workers & Pages > Create > Import a repository > this repo.
2. Root directory `apps/web`. Build command `npm ci && npm run cf:build`. Deploy command `npm run cf:deploy`.
3. Variables: `NEXT_PUBLIC_API_URL=https://<api>.onrender.com`, `NEXT_PUBLIC_APP_ENV=production` (also edit `apps/web/wrangler.jsonc`).
4. You get `https://refurbi-web.<account>.workers.dev`. Add that URL to the API's `CORS_ORIGINS`.
5. Fallback: if the Worker build fails, keep using Render free for the web (`render.yaml` is unchanged and still valid).
6. Custom domain is optional; the free workers.dev subdomain works until you buy one.

## 5. Cloudflare R2 (device photos)
1. Cloudflare > R2 > Create bucket `refurbi-media` (free 10 GB; may ask for a payment method on some accounts - if so, skip R2 and photos stay on local disk, which Render free wipes on redeploy; tell the builder).
2. Bucket > Settings > enable the public `r2.dev` URL. R2 > Manage API tokens > Create (Object Read & Write).
3. API env: `S3_ENDPOINT=https://<account>.r2.cloudflarestorage.com`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_PUBLIC_BASE=https://pub-xxxx.r2.dev`.

## 6. Brevo (email OTP, order mail)
1. brevo.com > free plan (300 emails/day, no card). SMTP & API > API keys > create.
2. Settings > Senders > add and verify your sender address.
3. API env: `BREVO_API_KEY`, `EMAIL_FROM`.

## 7. Backups (free)
- Neon free keeps a short point-in-time history (check the Neon console for the current window); do not rely on it alone.
- Weekly manual dump: `DATABASE_URL='postgresql://...direct...' sh services/api/scripts/backup.sh ~/refurbi-backups` (needs `pg_dump` 16+). Store the file in your Google Drive.
- Restore into an empty Neon branch/database: `pg_restore --no-owner --clean --if-exists -d "<target url>" file.dump`. Test a restore once before launch.

## 8. Optional free extras
Sentry free (errors): not wired yet. Google sign-in: create an OAuth client in Google Cloud console (free). WhatsApp: wa.me links need no account.

## Founder checklist
[you] GSTIN, legal name, address, UPI ID; [you] CA sign-off on the margin scheme; [you] grade/warranty/return terms; [you] counter details; [you] real product photos and prices.
