import { apiBaseUrl } from "@/lib/config";
import { LeadInbox } from "./LeadInbox";

export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <div className="space-y-4">
      <h1 className="font-display text-2xl font-bold">Exchange enquiries</h1>
      <LeadInbox apiBase={apiBaseUrl()} />
    </div>
  );
}
