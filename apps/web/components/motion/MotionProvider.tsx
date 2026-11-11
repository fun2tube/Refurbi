"use client";
import { LazyMotion, MotionConfig, domAnimation } from "motion/react";

/** Loads only the DOM animation features (small bundle). Use `m.*` components, not `motion.*`.
 *  reducedMotion="user" makes transform/layout animations instant for users who ask for less motion. */
export function MotionProvider({ children }: { children: React.ReactNode }) {
  return (
    <LazyMotion features={domAnimation} strict>
      <MotionConfig reducedMotion="user">{children}</MotionConfig>
    </LazyMotion>
  );
}
