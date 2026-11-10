import type { Metadata } from "next";
import { Inter, Manrope } from "next/font/google";
import "./globals.css";
import { DemoBanner } from "@/components/DemoBanner";
import { isPreview } from "@/lib/config";
import { siteUrl } from "@/lib/site";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const manrope = Manrope({ variable: "--font-manrope", subsets: ["latin"] });

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl()),
  title: { default: "Refurbi - checked and graded refurbished phones", template: "%s | Refurbi" },
  description: "Refurbished smartphones, checked and graded, with battery health, grade and price shown per phone.",
  openGraph: { siteName: "Refurbi", type: "website", locale: "en_IN" },
  robots: isPreview() ? { index: false, follow: false } : undefined,
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${manrope.variable} antialiased`}>
        <DemoBanner />
        {children}
      </body>
    </html>
  );
}
