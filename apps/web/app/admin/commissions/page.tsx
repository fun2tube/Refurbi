import { apiBaseUrl } from "@/lib/config";
import { Commissions } from "./Commissions";

export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <div className="space-y-4">
      <h1 className="font-display text-2xl font-bold">Counter commission</h1>
      <p className="text-sm text-midnight/70">
        Unsettled commission per counter. Assumes the counter collects the customer payment and owes Refurbi sales minus commission (to be confirmed).
      </p>
      <Commissions apiBase={apiBaseUrl()} />
    </div>
  );
}
