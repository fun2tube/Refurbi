import { apiBaseUrl } from "@/lib/config";
import { WarrantyLookup } from "./WarrantyLookup";

export const dynamic = "force-dynamic";
export const metadata = { title: "Check your warranty" };

export default function Page() {
  return (
    <div className="mx-auto max-w-md space-y-3 p-4">
      <h1 className="font-display text-2xl font-bold">Check your warranty</h1>
      <p className="text-sm text-midnight/70">Enter the mobile number used at purchase and your invoice number.</p>
      <WarrantyLookup apiBase={apiBaseUrl()} />
    </div>
  );
}
