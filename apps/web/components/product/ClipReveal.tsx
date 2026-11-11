"use client";
import { m } from "motion/react";
import { duration, ease } from "@/lib/motion";

/** Reveals content with a clip-path wipe (top -> bottom) when scrolled into view. */
export function ClipReveal({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <m.div
      className={className}
      initial={{ clipPath: "inset(0 0 100% 0)" }}
      whileInView={{ clipPath: "inset(0 0 0% 0)" }}
      viewport={{ once: true, margin: "0px 0px -8% 0px" }}
      transition={{ duration: duration.slow, ease: ease.out }}
    >
      {children}
    </m.div>
  );
}

/** List item that fades up with a stagger by index. */
export function RevealItem({ children, index = 0, className }: { children: React.ReactNode; index?: number; className?: string }) {
  return (
    <m.li
      className={className}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: duration.base, ease: ease.out, delay: Math.min(index * 0.06, 0.3) }}
    >
      {children}
    </m.li>
  );
}
