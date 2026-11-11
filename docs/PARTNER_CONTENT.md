# Partner catalogue content (demo data)

Phones from a partner's public Shopify catalogue are used as **demo catalogue content** in preview
(models, variants, CDN image URLs, and the partner price as the *demo* device price).

- Scope: phones only (`Refurbished Mobiles` + phone listings in `Pre Owned`; dead/combo/functional-issue
  listings, laptops, tablets and gadgets are skipped).
- Snapshot: `data/partners/budli/phones.json` (slim: id, title, type, price, up to 3 image URLs;
  no descriptions, links or partner name). A byte-identical packaged copy lives at
  `services/api/app/partners/phones_snapshot.json` because the API Docker context is `services/api`.
- Refresh: `cd services/api && uv run python scripts/fetch_partner_catalogue.py` (needs network), commit both files.
- Import: `app.partners.catalogue.import_snapshot`, run by `app.seed` only when `APP_ENV=preview`.
  Idempotent upsert keyed by a synthetic IMEI derived from the partner product id; prices update in place.
  Demo devices are AVAILABLE at the demo counters, grades/battery are placeholders, cost = 80% of price.
- Images: only `https://cdn.shopify.com/` URLs (hotlinked; `cdn.shopify.com` is in `next.config` remotePatterns).
- The partner's name and links are never shown in the UI or stored in the DB. Photos may carry the
  partner's own watermarks/boxes: **founder must review before any non-preview use** (licence,
  accuracy of condition/warranty). Not real stock, not real prices of ours.
