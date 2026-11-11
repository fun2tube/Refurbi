"use client";
import { m, useMotionValue, useSpring } from "motion/react";
import { spring } from "@/lib/motion";

/** Wrapper that gently pulls its child toward the pointer (fine pointers only; no effect on touch). */
export function Magnetic({ children, className }: { children: React.ReactNode; className?: string }) {
  const x = useSpring(useMotionValue(0), spring.soft);
  const y = useSpring(useMotionValue(0), spring.soft);
  return (
    <m.div
      className={className}
      style={{ x, y }}
      onPointerMove={(e) => {
        if (e.pointerType !== "mouse") return;
        const r = e.currentTarget.getBoundingClientRect();
        x.set((e.clientX - (r.left + r.width / 2)) * 0.2);
        y.set((e.clientY - (r.top + r.height / 2)) * 0.2);
      }}
      onPointerLeave={() => {
        x.set(0);
        y.set(0);
      }}
    >
      {children}
    </m.div>
  );
}
