"use client";
import { m } from "motion/react";
import { spring } from "@/lib/motion";

/** Tap squash + slight 3D tilt on press (touch and mouse). Transform only; instant under reduced motion. */
export function TapCard({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <m.div
      className={className}
      style={{ transformPerspective: 600 }}
      whileTap={{ scale: 0.965, rotateX: 4 }}
      transition={spring.snappy}
    >
      {children}
    </m.div>
  );
}
