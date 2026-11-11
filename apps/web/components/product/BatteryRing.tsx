"use client";
import { m } from "motion/react";
import { duration, ease } from "@/lib/motion";

/** Battery health ring: stroke draws in when scrolled into view. Shows the real % of the unit. */
export function BatteryRing({ percent }: { percent: number }) {
  const p = Math.max(0, Math.min(100, percent));
  return (
    <span className="relative inline-flex h-11 w-11 items-center justify-center" role="img" aria-label={`Battery health ${p}%`}>
      <svg viewBox="0 0 36 36" className="absolute inset-0 -rotate-90" aria-hidden>
        <circle cx="18" cy="18" r="15" fill="none" stroke="currentColor" strokeOpacity="0.15" strokeWidth="3" />
        <m.circle
          cx="18"
          cy="18"
          r="15"
          fill="none"
          stroke="#247C65"
          strokeWidth="3"
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          whileInView={{ pathLength: p / 100 }}
          viewport={{ once: true }}
          transition={{ duration: duration.slow, ease: ease.out }}
        />
      </svg>
      <span className="text-[11px] font-semibold tabular-nums" aria-hidden>
        {p}
      </span>
    </span>
  );
}
