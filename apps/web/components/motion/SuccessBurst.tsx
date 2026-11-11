"use client";
import { m } from "motion/react";
import { useEffect } from "react";
import { duration, ease } from "@/lib/motion";

/** Green ring burst + checkmark draw for success moments; short haptic tick on Android. Calm when reduced motion. */
export function SuccessBurst() {
  useEffect(() => {
    try {
      navigator.vibrate?.(20);
    } catch {}
  }, []);
  return (
    <svg viewBox="0 0 64 64" aria-hidden className="mb-2 h-14 w-14 text-brand" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <m.circle cx="32" cy="32" r="26" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: duration.slow, ease: ease.out }} />
      <m.path d="M20 33l9 9 16-18" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: duration.base, delay: 0.35, ease: ease.out }} />
      <m.circle cx="32" cy="32" r="26" strokeWidth="1.5" initial={{ scale: 0.8, opacity: 0.6 }} animate={{ scale: 1.5, opacity: 0 }} transition={{ duration: duration.slow, delay: 0.3 }} style={{ transformOrigin: "32px 32px" }} />
    </svg>
  );
}
