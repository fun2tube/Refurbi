import { apiBaseUrl } from "@/lib/config";

export const dynamic = "force-dynamic";

type ModelItem = { slug: string; name: string; brand: { name: string }; release_year: number | null };

async function load(): Promise<{ items: ModelItem[] } | { error: string }> {
  const base = apiBaseUrl();
  if (!base) return { error: "API URL is not configured." };
  try {
    const res = await fetch(`${base}/catalog/models?page_size=100`, { cache: "no-store" });
    if (!res.ok) return { error: `API returned ${res.status}.` };
    return { items: (await res.json()).items as ModelItem[] };
  } catch {
    return { error: "Could not reach the API (it may be waking up - retry in a minute)." };
  }
}

export default async function Catalogue() {
  const data = await load();
  return (
    <div className="mx-auto w-full max-w-6xl space-y-4 px-4 py-8">
      <h1 className="font-display text-2xl font-bold">Catalogue (demo)</h1>
      {"error" in data ? (
        <p className="text-sm text-midnight/70">{data.error}</p>
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((m) => (
            <li key={m.slug} className="rounded-lg border border-silver/40 bg-white p-4">
              <div className="text-xs uppercase tracking-wide text-silver">{m.brand.name}</div>
              <div className="font-display font-semibold">{m.name}</div>
              {m.release_year && <div className="text-sm text-midnight/70">{m.release_year}</div>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
