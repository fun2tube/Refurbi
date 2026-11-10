import type { MetadataRoute } from "next";
import { isPreview } from "@/lib/config";
import { siteUrl } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  // The preview shows demo data: keep it out of search engines.
  if (isPreview()) return { rules: [{ userAgent: "*", disallow: "/" }] };
  return {
    rules: [{ userAgent: "*", allow: "/", disallow: ["/admin", "/partner", "/preview", "/catalogue", "/cart"] }],
    sitemap: `${siteUrl()}/sitemap.xml`,
  };
}
