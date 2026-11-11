"use client";
import { m } from "motion/react";
import { duration, ease } from "@/lib/motion";
import { useReducedMotionSafe } from "./useReducedMotionSafe";

let hasMounted = false;

/** Route transition (used by app/(store)/template.tsx): brand-green curtain wipe + content rise, ~350ms.
 *  Skipped on the very first load and for reduced motion; the curtain never intercepts taps. */
export function PageTransition({ children }: { children: React.ReactNode }) {
  const reduced = useReducedMotionSafe();
  const animate = hasMounted && !reduced;
  hasMounted = true;
  if (!animate) return <>{children}</>;
  return (
    <>
      <m.div
        aria-hidden
        data-testid="page-curtain"
        className="pointer-events-none fixed inset-0 z-[60] bg-brand"
        initial={{ clipPath: "inset(0 0 0 0)" }}
        animate={{ clipPath: "inset(0 0 100% 0)" }}
        transition={{ duration: duration.base, ease: ease.curtain }}
      />
      <m.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: duration.base, ease: ease.out }}
      >
        {children}
      </m.div>
    </>
  );
}

/** Test helper. */
export function resetPageTransitionForTests() {
  hasMounted = false;
}
