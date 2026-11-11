"use client";
import { useEffect, useState } from "react";
import { cn } from "@/lib/cn";

/** Sticky header that condenses once scrolled: logo scales down, shadow appears. Height is fixed (no CLS). */
export function CondensingHeader({ children }: { children: React.ReactNode }) {
  const [condensed, setCondensed] = useState(false);
  useEffect(() => {
    const onScroll = () => setCondensed(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return (
    <header
      data-condensed={condensed}
      className={cn(
        "group sticky top-0 z-30 border-b border-silver/40 bg-porcelain/90 backdrop-blur transition-shadow duration-200",
        condensed && "shadow-[0_8px_24px_-12px_rgb(17_19_24/0.25)]",
      )}
    >
      {children}
    </header>
  );
}
