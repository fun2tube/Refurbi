import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Container } from "@/components/store/Container";
import { apiGet } from "@/lib/api";
import { formatRupees } from "@/lib/money";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: "Track your order", robots: { index: false, follow: false } };

type Order = {
  number: string; status: string; total_paise: number; carrier: string | null; tracking_no: string | null;
  items: { title: string; price_paise: number }[]; timeline: { status: string; note: string; at: string }[];
};

export default async function OrderPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const r = await apiGet<Order>(`/public/orders/${encodeURIComponent(token)}`);
  if (!r.ok) {
    if (r.error === "not_found") notFound();
    return <Container className="py-10"><p role="alert">We could not load your order right now. Please retry in a minute.</p></Container>;
  }
  const o = r.data;
  return (
    <Container className="py-6 md:py-10">
      <h1 className="font-display text-2xl font-bold md:text-3xl">Order {o.number}</h1>
      <p className="mt-1 text-sm text-midnight/70">Status: <b>{o.status}</b> · Total {formatRupees(o.total_paise)}</p>
      {o.tracking_no && <p className="mt-1 text-sm">Tracking: {o.carrier} {o.tracking_no}</p>}
      <ul className="mt-4 space-y-1 text-sm">
        {o.items.map((i, n) => <li key={n}>{i.title} - {formatRupees(i.price_paise)}</li>)}
      </ul>
      <h2 className="mt-6 font-display text-lg font-semibold">Timeline</h2>
      <ol className="mt-2 space-y-1 text-sm">
        {o.timeline.map((t, n) => (
          <li key={n}>{new Date(t.at).toLocaleString("en-IN")} - {t.status}{t.note ? ` (${t.note})` : ""}</li>
        ))}
      </ol>
    </Container>
  );
}
