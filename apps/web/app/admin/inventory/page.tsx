import { apiBaseUrl } from "@/lib/config";
import { InventoryTable } from "./InventoryTable";

export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <div className="space-y-4">
      <h1 className="font-display text-2xl font-bold">Inventory</h1>
      <InventoryTable apiBase={apiBaseUrl()} />
    </div>
  );
}
