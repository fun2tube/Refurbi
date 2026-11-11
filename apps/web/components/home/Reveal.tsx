"use client";
import { m } from "motion/react";
import { duration, ease } from "@/lib/motion";

/** Fade-up when scrolled into view (once). Reduced motion: MotionConfig makes it instant. */
export function Reveal({
  children,
  delay = 0,
  className,
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <m.div
      className={className}
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "0px 0px -10% 0px" }}
      transition={{ duration: duration.slow, ease: ease.out, delay }}
    >
      {children}
    </m.div>
  );
}
