import type { Metadata } from "next";
import Link from "next/link";
import { Container } from "@/components/store/Container";
import { apiBaseUrl } from "@/lib/config";
import { AccountClient } from "./AccountClient";

export const dynamic = "force-dynamic";
export const metadata: Metadata = {
  title: "My orders",
  robots: { index: false, follow: true },
  alternates: { canonical: "/account" },
};

export default function AccountPage() {
  return (
    <Container className="py-6 md:py-10">
      <h1 className="font-display text-2xl font-bold md:text-3xl">My orders</h1>
      <p className="mt-1 max-w-2xl text-sm text-midnight/70">
        Enter the email you used at checkout. We send a one-time code - no password needed. To check a warranty,
        use <Link className="text-brand underline" href="/warranty-check">warranty check</Link>.
      </p>
      <AccountClient apiBase={apiBaseUrl()} />
    </Container>
  );
}
