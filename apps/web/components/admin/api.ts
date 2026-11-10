"use client";

export const TOKEN_KEY = "refurbi_access_token";

export function getToken(): string {
  try {
    return sessionStorage.getItem(TOKEN_KEY) ?? "";
  } catch {
    return "";
  }
}

export type ApiResult<T> = { ok: true; data: T } | { ok: false; status: number; error: string };

/** Authenticated call to the admin API. Never throws. */
export async function adminFetch<T>(
  apiBase: string,
  path: string,
  init: RequestInit & { json?: unknown } = {},
): Promise<ApiResult<T>> {
  const token = getToken();
  if (!token) return { ok: false, status: 401, error: "Please sign in first." };
  const headers: Record<string, string> = { Authorization: `Bearer ${token}` };
  let body = init.body;
  if (init.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(init.json);
  }
  try {
    const res = await fetch(`${apiBase}${path}`, { ...init, headers: { ...headers, ...(init.headers as object) }, body });
    if (res.status === 204) return { ok: true, data: undefined as T };
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data?.error?.message ?? (Array.isArray(data?.detail) ? "Please check the form values." : `Request failed (${res.status}).`);
      return { ok: false, status: res.status, error: res.status === 401 ? "Session expired - sign in again." : msg };
    }
    return { ok: true, data: data as T };
  } catch {
    return { ok: false, status: 0, error: "Could not reach the API (it may be waking up - retry in a minute)." };
  }
}

export function qs(params: Record<string, string | number | undefined>): string {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== "") p.set(k, String(v));
  const s = p.toString();
  return s ? `?${s}` : "";
}
