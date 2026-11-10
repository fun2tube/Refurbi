import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    // Product pages live at /refurbished-<model-slug>. Next cannot express a prefixed dynamic
    // segment, so rewrite to /product/<slug>. Real files (e.g. /refurbished-mobiles) take priority.
    return [{ source: "/refurbished-:slug", destination: "/product/:slug" }];
  },
};

export default nextConfig;
