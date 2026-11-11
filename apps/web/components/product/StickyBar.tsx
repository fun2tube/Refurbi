"use client";
import { m } from "motion/react";
import { spring } from "@/lib/motion";

/** Mobile sticky Reserve/WhatsApp bar: springs up from below after first paint. */
export function StickyBar({ children }: { children: React.ReactNode }) {
  return (
    <m.div
      className="fixed inset-x-0 bottom-16 z-30 flex gap-2 border-t border-silver/40 bg-porcelain/95 p-3 backdrop-blur md:hidden"
      initial={{ y: 120 }}
      animate={{ y: 0 }}
      transition={{ ...spring.sheet, delay: 0.4 }}
    >
      {children}
    </m.div>
  );
}
