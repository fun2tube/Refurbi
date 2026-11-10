import type { Metadata } from "next";
import { Container } from "@/components/store/Container";
import { apiBaseUrl } from "@/lib/config";
import { ExchangeForm } from "./ExchangeForm";

export const dynamic = "force-dynamic";
export const metadata: Metadata = {
  title: "Exchange your old phone",
  description: "Answer a few questions to get an indicative exchange range for your old phone, then confirm it in store.",
  alternates: { canonical: "/exchange" },
};

export default function Exchange() {
  return (
    <Container className="py-6 md:py-10">
      <h1 className="font-display text-2xl font-bold md:text-3xl">Exchange your old phone</h1>
      <p className="mt-1 max-w-2xl text-sm text-midnight/70">
        Answer a few questions for an indicative range. The final offer is confirmed after an in-store inspection.
      </p>
      <ExchangeForm apiBase={apiBaseUrl()} />
    </Container>
  );
}
