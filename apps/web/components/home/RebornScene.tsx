"use client";
import { m, useMotionValue, useScroll, useTransform, type MotionValue } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { DeviceArt } from "@/components/store/DeviceArt";
import { useReducedMotionSafe } from "@/components/motion/useReducedMotionSafe";

function Phone({ p }: { p: MotionValue<number> }) {
  const worn = useTransform(p, [0, 1], [1, 0]);
  const glow = useTransform(p, [0, 1], [0.1, 1]);
  const scale = useTransform(p, [0, 1], [0.94, 1.04]);
  return (
    <div className="relative mx-auto h-72 md:h-96">
      <m.div style={{ opacity: glow }} aria-hidden className="absolute inset-x-4 inset-y-8 rounded-full bg-brand/40 blur-3xl" />
      <m.div style={{ scale }} className="relative mx-auto aspect-[120/200] h-full">
        <DeviceArt seed={2} className="!w-full" label="Phone going from worn to restored" />
        {/* worn layer: scratches + dullness fade away as p -> 1 */}
        <m.svg style={{ opacity: worn }} viewBox="0 0 120 200" aria-hidden className="absolute inset-0 h-full w-full">
          <rect x="14" y="8" width="92" height="184" rx="14" fill="#000" opacity="0.35" />
          <g stroke="#cfd5da" strokeOpacity="0.7" strokeWidth="0.8" strokeLinecap="round">
            <path d="M24 40l30 22M70 20l18 40M30 150l40-18M80 130l20 30M40 90l22-6" />
          </g>
        </m.svg>
      </m.div>
    </div>
  );
}

const STEPS = ["Received", "Checked", "Restored", "Ready"];

/** Scene 2: pinned scroll scene. Reduced motion (or no JS pinning): a draggable before/after slider instead. */
export function RebornScene() {
  // Calm until mounted: motion reads matchMedia synchronously on the client, which would break hydration.
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const reduced = useReducedMotionSafe() || !mounted;
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end end"] });
  const manual = useMotionValue(0.5);
  const p = reduced ? manual : scrollYProgress;
  const label = useTransform(p, (v) => STEPS[Math.min(3, Math.floor(v * 4))]);

  return (
    <section aria-labelledby="reborn" className="bg-midnight text-porcelain">
      <div ref={ref} className={reduced ? "" : "h-[220vh]"}>
        <div className={reduced ? "py-12" : "sticky top-0 flex min-h-[100svh] items-center py-12"}>
          <div className="mx-auto w-full max-w-6xl px-4">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-silver">Second life</p>
            <h2 id="reborn" className="mt-2 max-w-md font-display text-3xl font-bold md:text-4xl">
              Every phone is checked, cleaned and brought back.
            </h2>
            <p className="mt-2 max-w-md text-silver">
              {reduced ? "Drag to compare worn and restored." : "Keep scrolling to watch one phone come back."} Cosmetic
              condition is graded honestly and shown on every listing.
            </p>
            <div className="mt-6">
              <Phone p={p} />
            </div>
            <m.p className="mt-4 text-center font-display text-lg font-semibold text-brand" aria-live="off">
              {label}
            </m.p>
            {reduced && (
              <input
                type="range"
                min={0}
                max={100}
                defaultValue={50}
                aria-label="Worn to restored"
                onChange={(e) => manual.set(Number(e.target.value) / 100)}
                className="mx-auto mt-4 block h-11 w-full max-w-xs accent-[#247C65]"
              />
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
