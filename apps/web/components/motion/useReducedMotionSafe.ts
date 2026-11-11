"use client";
import { useReducedMotion } from "motion/react";

/** true when the user prefers reduced motion. Server/first render is treated as reduced (calm by default). */
export function useReducedMotionSafe(): boolean {
  return useReducedMotion() ?? true;
}
