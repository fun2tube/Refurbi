"use client";
import { m } from "motion/react";
import { useState } from "react";
import { DeviceArt } from "@/components/store/DeviceArt";
import { spring } from "@/lib/motion";

/** 3D card-flip gallery: front = phone, back = quick facts. Button toggles (keyboard + touch). */
export function FlipGallery({ seed, name, facts }: { seed: number; name: string; facts: string[] }) {
  const [back, setBack] = useState(false);
  return (
    <div className="relative h-72 md:h-[28rem] [perspective:1000px]">
      <m.div
        className="relative h-full w-full [transform-style:preserve-3d]"
        initial={false}
        animate={{ rotateY: back ? 180 : 0 }}
        transition={spring.soft}
      >
        <div className="absolute inset-0 flex items-center justify-center rounded-3xl bg-gradient-to-b from-white to-silver/25 py-6 [backface-visibility:hidden]">
          <DeviceArt seed={seed} label={`${name} illustration`} />
        </div>
        <div className="absolute inset-0 flex flex-col justify-center gap-3 rounded-3xl bg-midnight p-8 text-porcelain [backface-visibility:hidden] [transform:rotateY(180deg)]">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-silver">At a glance</p>
          <ul className="space-y-2 font-display text-lg">
            {facts.map((f) => (
              <li key={f}>✓ {f}</li>
            ))}
          </ul>
        </div>
      </m.div>
      <button
        type="button"
        onClick={() => setBack((b) => !b)}
        aria-pressed={back}
        className="absolute bottom-3 right-3 inline-flex h-11 items-center rounded-full bg-midnight/80 px-4 text-sm font-medium text-porcelain backdrop-blur"
      >
        {back ? "Show phone" : "At a glance"}
      </button>
    </div>
  );
}
