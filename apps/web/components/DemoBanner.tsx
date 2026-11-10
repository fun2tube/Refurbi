import { isPreview } from "@/lib/config";

/** Shown on every page when APP_ENV=preview. */
export function DemoBanner() {
  if (!isPreview()) return null;
  return (
    <div
      role="status"
      className="bg-midnight px-4 py-1.5 text-center text-xs font-medium tracking-wide text-porcelain"
    >
      Demo data - this is a preview. Nothing here is real stock, pricing or customers.
    </div>
  );
}
