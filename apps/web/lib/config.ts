/** Normalise a base URL: add https:// when the scheme is missing (some hosts give bare hosts),
 *  and strip trailing slashes. */
export function normaliseBaseUrl(raw: string | undefined | null): string {
  const v = (raw ?? "").trim().replace(/\/+$/, "");
  if (!v) return "";
  return /^https?:\/\//i.test(v) ? v : `https://${v}`;
}

/** API base URL from NEXT_PUBLIC_API_URL. Falls back to a local API only in development. */
export function apiBaseUrl(env: Record<string, string | undefined> = process.env): string {
  const fromEnv = normaliseBaseUrl(env.NEXT_PUBLIC_API_URL);
  if (fromEnv) return fromEnv;
  return env.NODE_ENV === "development" ? "http://localhost:8000" : "";
}

export function isPreview(env: Record<string, string | undefined> = process.env): boolean {
  return (env.APP_ENV ?? env.NEXT_PUBLIC_APP_ENV) === "preview";
}
