import { apiBaseUrl } from "@/lib/config";
import { DeviceDetail } from "./DeviceDetail";

export const dynamic = "force-dynamic";

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <DeviceDetail apiBase={apiBaseUrl()} id={Number(id)} />;
}
