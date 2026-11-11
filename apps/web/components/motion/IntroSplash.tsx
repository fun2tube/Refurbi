"use client";
import { useEffect, useState } from "react";
import { AnimatePresence, m } from "motion/react";
import { useReducedMotionSafe } from "./useReducedMotionSafe";

const KEY = "refurbi_intro_seen";
export const INTRO_MS = 1100;

/** First-visit logo intro: 'refurbi' draws in, then the dot pulses green. <=1.2s, tap anywhere to skip,
 *  never shown to reduced-motion users or on repeat visits. Content renders beneath from the start. */
export function IntroSplash() {
  const reduced = useReducedMotionSafe();
  const [show, setShow] = useState(false);

  useEffect(() => {
    let seen = false;
    try {
      seen = localStorage.getItem(KEY) === "1";
      localStorage.setItem(KEY, "1");
    } catch {
      seen = true; // storage blocked: never nag
    }
    if (seen || reduced) return;
    setShow(true);
    const t = setTimeout(() => setShow(false), INTRO_MS);
    return () => clearTimeout(t);
  }, [reduced]);

  return (
    <AnimatePresence>
      {show && (
        <m.button
          type="button"
          aria-label="Skip intro"
          data-testid="intro-splash"
          onClick={() => setShow(false)}
          className="film-grain fixed inset-0 z-[70] flex items-center justify-center bg-midnight"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, transition: { duration: 0.2 } }}
        >
          <svg viewBox="0 0 220 60" className="w-48" role="img" aria-label="refurbi.">
            <text x="0" y="44" className="intro-draw font-display" fontSize="48" fontWeight="700" fill="none" stroke="#F7F7F5" strokeWidth="1.2">
              refurbi
            </text>
            <circle cx="203" cy="40" r="4.5" className="intro-dot" fill="#247C65" />
          </svg>
        </m.button>
      )}
    </AnimatePresence>
  );
}
