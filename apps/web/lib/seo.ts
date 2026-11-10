import { siteUrl, SITE_NAME } from "./site";

export type Crumb = { name: string; path: string };

export function breadcrumbLd(items: Crumb[], base: string = siteUrl()) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((c, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: c.name,
      item: `${base}${c.path}`,
    })),
  };
}

export function organizationLd(base: string = siteUrl()) {
  // Only facts we actually have. Legal name, address and contact points are added once the
  // founder supplies them (see PROGRESS.md Founder inputs).
  return { "@context": "https://schema.org", "@type": "Organization", name: SITE_NAME, url: base };
}

export function websiteLd(base: string = siteUrl()) {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: SITE_NAME,
    url: base,
    potentialAction: {
      "@type": "SearchAction",
      target: `${base}/refurbished-mobiles?q={search_term_string}`,
      "query-input": "required name=search_term_string",
    },
  };
}

/** JSON for a <script type="application/ld+json">: escape "<" so content can never close the tag. */
export function ldJson(obj: unknown): string {
  return JSON.stringify(obj).replace(/</g, "\\u003c");
}

/** Old/alternative URLs -> canonical URLs (301). Keep in sync with real routes. */
export const REDIRECTS: { source: string; destination: string }[] = [
  { source: "/mobiles", destination: "/refurbished-mobiles" },
  { source: "/phones", destination: "/refurbished-mobiles" },
  { source: "/shop", destination: "/refurbished-mobiles" },
  { source: "/refurbished-phones", destination: "/refurbished-mobiles" },
  { source: "/store-locator", destination: "/stores" },
  { source: "/about-us", destination: "/about" },
  { source: "/contact-us", destination: "/contact" },
  { source: "/faqs", destination: "/faq" },
  { source: "/warranty-policy", destination: "/warranty" },
  { source: "/return-policy", destination: "/returns" },
];
