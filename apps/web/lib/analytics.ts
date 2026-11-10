/**
 * Analytics (T35). GA4 is loaded ONLY after the visitor accepts (consent), and only when
 * NEXT_PUBLIC_GA_MEASUREMENT_ID is set. Cloudflare Web Analytics (NEXT_PUBLIC_CF_BEACON_TOKEN) is
 * cookieless and needs no consent. Events carry unit ids and rupee values only - never PII or IMEI.
 */
export const CONSENT_KEY = "refurbi.consent.v1";
export type Consent = "granted" | "denied";
type Env = Record<string, string | undefined>;

export function gaId(env: Env = process.env): string {
  const v = (env.NEXT_PUBLIC_GA_MEASUREMENT_ID ?? "").trim();
  return /^G-[A-Z0-9]{4,}$/.test(v) ? v : "";
}

export function cfBeaconToken(env: Env = process.env): string {
  const v = (env.NEXT_PUBLIC_CF_BEACON_TOKEN ?? "").trim();
  return /^[a-f0-9]{16,64}$/i.test(v) ? v : "";
}

export function readConsent(): Consent | null {
  try {
    const v = window.localStorage.getItem(CONSENT_KEY);
    return v === "granted" || v === "denied" ? v : null;
  } catch {
    return null;
  }
}

export function writeConsent(c: Consent): void {
  try {
    window.localStorage.setItem(CONSENT_KEY, c);
  } catch {
    /* private mode: the choice just applies to this page view */
  }
  window.dispatchEvent(new Event("refurbi-consent"));
}

type Gtag = (...a: unknown[]) => void;
type Params = Record<string, unknown>;

/** Sends an event only when consent was granted AND GA4 is configured/loaded. Otherwise a no-op. */
export function track(event: string, params: Params = {}): boolean {
  if (typeof window === "undefined" || !gaId() || readConsent() !== "granted") return false;
  const g = (window as unknown as { gtag?: Gtag }).gtag;
  if (!g) return false;
  g("event", event, params);
  return true;
}

const rupees = (paise: number) => Math.round(paise) / 100;
const item = (unitId: number, paise?: number | null) => ({
  item_id: String(unitId),
  ...(paise != null ? { price: rupees(paise) } : {}),
  quantity: 1,
});

export const events = {
  addToCart: (unitId: number): Params => ({ currency: "INR", items: [item(unitId)] }),
  beginCheckout: (items: { unit_id: number; price_paise: number }[], totalPaise: number): Params => ({
    currency: "INR",
    value: rupees(totalPaise),
    items: items.map((i) => item(i.unit_id, i.price_paise)),
  }),
  purchase: (token: string, items: { unit_id: number; price_paise: number }[], totalPaise: number): Params => ({
    transaction_id: token,
    currency: "INR",
    value: rupees(totalPaise),
    items: items.map((i) => item(i.unit_id, i.price_paise)),
  }),
  whatsappClick: (path: string): Params => ({ method: "whatsapp", page_path: path }),
};

/** Core Web Vitals -> GA4 (consent-gated like everything else). */
export function vitalsParams(m: { name: string; value: number; id: string; rating?: string }): Params {
  return {
    metric_name: m.name,
    metric_id: m.id,
    metric_value: m.name === "CLS" ? Math.round(m.value * 1000) / 1000 : Math.round(m.value),
    metric_rating: m.rating ?? "",
  };
}
