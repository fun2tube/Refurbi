import { apiBaseUrl } from "@/lib/config";
import { WarrantyAdmin } from "./WarrantyAdmin";

export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <div className="space-y-4">
      <h1 className="font-display text-2xl font-bold">Warranty and claims</h1>
      <WarrantyAdmin apiBase={apiBaseUrl()} />
    </div>
  );
}
