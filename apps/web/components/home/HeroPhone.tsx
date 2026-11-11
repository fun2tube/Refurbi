"use client";
import { m, useScroll, useTransform } from "motion/react";
import { useRef } from "react";
import { DeviceArt } from "@/components/store/DeviceArt";
import { duration, ease } from "@/lib/motion";

/** Phone rises from the dark, gets a rim-light sweep, and rotates slowly as the hero scrolls away. */
export function HeroPhone() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
  const rotateY = useTransform(scrollYProgress, [0, 1], [-8, 28]);
  const y = useTransform(scrollYProgress, [0, 1], [0, 40]);
  return (
    <div ref={ref} className="relative flex h-full items-end justify-center [perspective:900px]">
      <m.div
        initial={{ opacity: 0, y: 70 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: duration.scene, ease: ease.out }}
        className="relative h-full"
      >
        <m.div style={{ rotateY, y }} className="relative h-full overflow-hidden rounded-[2rem]">
          <DeviceArt seed={1} className="relative -rotate-3" label="Phone rising from the dark" />
          <div
            aria-hidden
            className="light-sweep pointer-events-none absolute inset-y-0 left-0 w-1/3 bg-gradient-to-r from-transparent via-white/25 to-transparent"
          />
        </m.div>
      </m.div>
    </div>
  );
}
