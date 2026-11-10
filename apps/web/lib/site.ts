import { normaliseBaseUrl } from "./config";

export const SITE_NAME = "Refurbi";

/** Public site origin for canonical URLs / sitemap. Set NEXT_PUBLIC_SITE_URL in production. */
export function siteUrl(env: Record<string, string | undefined> = process.env): string {
  return normaliseBaseUrl(env.NEXT_PUBLIC_SITE_URL) || "https://refurbi-web.onrender.com";
}

/** WhatsApp number (digits, with country code) from env. PLACEHOLDER until the founder supplies the real one. */
export function whatsappNumber(env: Record<string, string | undefined> = process.env): string {
  return (env.NEXT_PUBLIC_WHATSAPP_NUMBER ?? "").replace(/\D/g, "");
}

export function hasRealWhatsapp(env: Record<string, string | undefined> = process.env): boolean {
  return whatsappNumber(env).length >= 10;
}

/** wa.me link with a prefilled message. Falls back to the bare wa.me page when no number is set. */
export function whatsappLink(message: string, env: Record<string, string | undefined> = process.env): string {
  const n = whatsappNumber(env);
  const q = `text=${encodeURIComponent(message)}`;
  return n ? `https://wa.me/${n}?${q}` : `https://wa.me/?${q}`;
}
