import type { Metadata } from "next";
import { Listing } from "@/components/store/Listing";
import type { SP } from "@/lib/listing";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Refurbished mobile phones",
  description: "Browse checked and graded refurbished smartphones with battery health, grade and price shown per phone.",
  alternates: { canonical: "/refurbished-mobiles" },
};

export default async function Page({ searchParams }: { searchParams: Promise<SP> }) {
  return (
    <Listing
      basePath="/refurbished-mobiles"
      title="Refurbished mobile phones"
      intro="Every listing is one real phone, with its own grade, battery health and price."
      sp={await searchParams}
    />
  );
}
