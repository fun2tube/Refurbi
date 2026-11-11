import { apiGet } from "@/lib/api";
import { ApiError } from "@/components/store/ApiError";

export const dynamic = "force-dynamic";

type ModelItem = { slug: string; name: string; brand: { name: string }; release_year: number | null };

export default async function Catalogue() {
  const r = await apiGet<{ items: ModelItem[] }>("/catalog/models?page_size=100", { cache: true });
  return (
    <div className="mx-auto w-full max-w-6xl space-y-4 px-4 py-8">
      <h1 className="font-display text-2xl font-bold">Catalogue (demo)</h1>
      {!r.ok ? (
        <ApiError error={r.error} waking={r.waking} />
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {r.data.items.map((m) => (
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
