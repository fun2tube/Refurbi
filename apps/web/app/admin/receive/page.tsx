import { apiBaseUrl } from "@/lib/config";
import { ReceiveStock } from "./ReceiveStock";

export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <div className="space-y-4">
      <h1 className="font-display text-2xl font-bold">Receive stock</h1>
      <ReceiveStock apiBase={apiBaseUrl()} />
    </div>
  );
}
