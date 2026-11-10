import type { Metadata } from "next";
import { Container } from "@/components/store/Container";
import { apiBaseUrl } from "@/lib/config";
import { CartClient } from "./CartClient";

export const dynamic = "force-dynamic";
export const metadata: Metadata = {
  title: "Your cart",
  robots: { index: false, follow: true },
  alternates: { canonical: "/cart" },
};

export default function CartPage() {
  return (
    <Container className="py-6 md:py-10">
      <h1 className="font-display text-2xl font-bold md:text-3xl">Your cart</h1>
      <p className="mt-1 max-w-2xl text-sm text-midnight/70">
        Checking out holds your phones for 15 minutes. Online payment is coming soon; until then you can reserve
        for store pickup from any phone page.
      </p>
      <CartClient apiBase={apiBaseUrl()} />
    </Container>
  );
}
