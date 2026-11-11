"use client";
import { m } from "motion/react";
import { DeviceArt } from "@/components/store/DeviceArt";
import { duration, ease } from "@/lib/motion";

const POINTS = [
  { label: "Screen", x: 60, y: 60 },
  { label: "Battery", x: 60, y: 120 },
  { label: "Camera", x: 90, y: 24 },
  { label: "Ports", x: 60, y: 188 },
];

/** Scene 3: layered phone, checkpoint markers draw in, battery bar fills. Example values only. */
export function InspectedScene() {
  return (
    <section aria-labelledby="inspected" className="bg-midnight pb-14 text-porcelain">
      <div className="mx-auto grid w-full max-w-6xl items-center gap-8 px-4 md:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-silver">Inspected</p>
          <h2 id="inspected" className="mt-2 font-display text-3xl font-bold">
            Every checkpoint, one by one.
          </h2>
          <ul className="mt-4 space-y-1 text-silver">
            {POINTS.map((p) => (
              <li key={p.label}>✓ {p.label}</li>
            ))}
          </ul>
          <div className="mt-6" role="img" aria-label="Example battery health bar">
            <div className="flex justify-between text-xs text-silver">
              <span>Battery health (example)</span>
              <span>every listing shows the real figure</span>
            </div>
            <div className="mt-2 h-3 overflow-hidden rounded-full bg-white/10">
              <m.div
                className="h-full origin-left rounded-full bg-brand"
                style={{ width: "86%" }}
                initial={{ scaleX: 0 }}
                whileInView={{ scaleX: 1 }}
                viewport={{ once: true }}
                transition={{ duration: duration.scene, ease: ease.out }}
              />
            </div>
          </div>
        </div>
        <div className="relative mx-auto h-72 md:h-96">
          <div className="relative mx-auto aspect-[120/200] h-full">
            <DeviceArt seed={1} className="!w-full" label="Phone with inspection checkpoints" />
            <svg viewBox="0 0 120 200" aria-hidden className="absolute inset-0 h-full w-full">
              {POINTS.map((p, i) => (
                <m.circle
                  key={p.label}
                  cx={p.x}
                  cy={p.y}
                  r="7"
                  fill="none"
                  stroke="#2fa88a"
                  strokeWidth="2"
                  initial={{ pathLength: 0, opacity: 0 }}
                  whileInView={{ pathLength: 1, opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: duration.slow, delay: 0.2 + i * 0.25, ease: ease.out }}
                />
              ))}
            </svg>
          </div>
        </div>
      </div>
    </section>
  );
}
