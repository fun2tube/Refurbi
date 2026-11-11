"use client";
import { animate, useInView, useMotionValue, useTransform, m } from "motion/react";
import { useEffect, useRef } from "react";

/** Counts 0 -> value when scrolled into view. SSR shows the final number (no layout shift, works without JS). */
export function CountUp({ value }: { value: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const mv = useMotionValue(value);
  const text = useTransform(mv, (v) => Math.round(v).toLocaleString("en-IN"));
  useEffect(() => {
    if (!inView) return;
    mv.set(0);
    const c = animate(mv, value, { duration: 1.2, ease: [0.22, 1, 0.36, 1] });
    return () => c.stop();
  }, [inView, value, mv]);
  return (
    <span ref={ref}>
      <m.span>{text}</m.span>
    </span>
  );
}
