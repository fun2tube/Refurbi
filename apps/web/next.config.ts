import type { NextConfig } from "next";
import { REDIRECTS } from "./lib/seo";

const SECURITY_HEADERS = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  { key: "Strict-Transport-Security", value: "max-age=31536000" },
];

const nextConfig: NextConfig = {
  // Self-contained server bundle (~10x smaller RSS than `next start`); see render.yaml.
  output: "standalone",
  poweredByHeader: false,
  images: { remotePatterns: [{ protocol: "https", hostname: "cdn.shopify.com" }] },
  async headers() {
    // CSP is intentionally not set yet (Razorpay checkout + OSM tiles + GA4 need a tuned allowlist; see docs/SECURITY.md).
    return [{ source: "/:path*", headers: SECURITY_HEADERS }];
  },
  async rewrites() {
    // Product pages live at /refurbished-<model-slug>. Next cannot express a prefixed dynamic
    // segment, so rewrite to /product/<slug>. Real files (e.g. /refurbished-mobiles) take priority.
    return [{ source: "/refurbished-:slug", destination: "/product/:slug" }];
  },
  async redirects() {
    return REDIRECTS.map((r) => ({ ...r, permanent: true }));
  },
};

export default nextConfig;
