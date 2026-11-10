/** Map adapter (D9: integrations behind adapters, fake in dev). A real Google Maps adapter plugs in
 *  later via NEXT_PUBLIC_MAPS_PROVIDER; until a store has verified coordinates, no map is drawn. */
export type MapView = { kind: "placeholder"; note: string } | { kind: "link"; href: string; label: string };

export function mapFor(store: { name: string; city: string }, provider: string | undefined = process.env.NEXT_PUBLIC_MAPS_PROVIDER): MapView {
  if (provider === "google-link") {
    const q = encodeURIComponent(`${store.name} ${store.city}`);
    return { kind: "link", href: `https://www.google.com/maps/search/?api=1&query=${q}`, label: "Open in Google Maps" };
  }
  return { kind: "placeholder", note: "Map and exact address will appear here once the store is verified." };
}
