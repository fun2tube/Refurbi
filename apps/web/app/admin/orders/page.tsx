import { apiBaseUrl } from "@/lib/config";
import { OrdersAdmin } from "./OrdersAdmin";

export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <div className="space-y-4">
      <h1 className="font-display text-2xl font-bold">Online orders</h1>
      <OrdersAdmin apiBase={apiBaseUrl()} />
    </div>
  );
}
