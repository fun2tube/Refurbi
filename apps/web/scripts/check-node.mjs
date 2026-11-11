// Fails fast with a clear message when the build Node is too old for Tailwind v4 (needs require(esm)).
const [maj, min] = process.versions.node.split(".").map(Number);
const ok = maj > 22 || (maj === 22 && min >= 12) || (maj === 20 && min >= 19);
console.log(`[check-node] building with Node ${process.versions.node}`);
if (!ok) {
  console.error("Node >= 22.12 (or 20.19) required. Set NODE_VERSION=22 on Render (render.yaml envVars / .node-version).");
  process.exit(1);
}
