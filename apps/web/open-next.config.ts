// OpenNext (Cloudflare Workers) config. Default settings are enough for Refurbi: no ISR cache
// bucket is needed on the free plan. See docs/GO_LIVE_FREE.md.
import { defineCloudflareConfig } from "@opennextjs/cloudflare";

export default defineCloudflareConfig();
