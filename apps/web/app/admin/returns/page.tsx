import { apiBaseUrl } from "@/lib/config";
import { ReturnsAdmin } from "./ReturnsAdmin";

export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <div className="space-y-4">
      <h1 className="font-display text-2xl font-bold">Returns and refunds</h1>
      <ReturnsAdmin apiBase={apiBaseUrl()} />
    </div>
  );
}
