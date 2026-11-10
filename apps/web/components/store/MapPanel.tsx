import { mapFor } from "@/lib/maps";

export function MapPanel({ name, city }: { name: string; city: string }) {
  const v = mapFor({ name, city });
  return (
    <div className="flex h-40 items-center justify-center rounded-2xl border border-dashed border-silver bg-white p-4 text-center text-sm text-midnight/70">
      {v.kind === "link" ? (
        <a href={v.href} target="_blank" rel="noopener noreferrer" className="font-medium text-brand underline">
          {v.label}
        </a>
      ) : (
        v.note
      )}
    </div>
  );
}
